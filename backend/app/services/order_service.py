"""OrderService — checkout and order history business logic.

Checkout executes within a DB savepoint for atomicity:
stock validation, deduction, product snapshot, order creation,
and cart clearing all succeed or roll back together.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductTranslation
from app.schemas.order import CheckoutRequest, OrderItemResponse, OrderResponse

logger = logging.getLogger(__name__)


class StockInsufficientError(ValueError):
    """Raised when one or more cart items exceed available stock."""


class CartEmptyError(ValueError):
    """Raised when attempting checkout with an empty cart."""


class OrderService:
    """Encapsulates checkout and order history business logic."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def checkout(
        self,
        session: AsyncSession,
        user_id: UUID,
        shipping_address: dict,
    ) -> OrderResponse:
        """Convert the user's cart into an order atomically.

        Flow:
        1. Load cart items with product data
        2. Validate cart is not empty
        3. Begin nested transaction (savepoint)
        4. For each item: atomically deduct stock, snapshot product data
        5. Create Order + OrderItems
        6. Clear cart
        7. Commit savepoint

        Raises:
            CartEmptyError: cart has no items → 400
            StockInsufficientError: any item has insufficient stock → 409
            ValueError: a product referenced in the cart no longer exists
        """
        # 1. Load cart items with product translations for snapshots
        cart_items = await self._load_cart_with_products(session, user_id)

        # 2. Validate
        if not cart_items:
            raise CartEmptyError("Cart is empty")

        # 3. Begin savepoint
        savepoint = await session.begin_nested()
        try:
            # 4. Validate stock and build order data
            total, order_items_data = await self._process_checkout_items(
                session, cart_items
            )

            # 5. Create order
            order = Order(
                user_id=user_id,
                total=total,
                shipping_address=shipping_address,
            )
            session.add(order)
            await session.flush()

            # Create order items with product snapshots
            for oi_data in order_items_data:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=oi_data["product_id"],
                    product_snapshot=oi_data["product_snapshot"],
                    quantity=oi_data["quantity"],
                    price=oi_data["price"],
                )
                session.add(order_item)
            await session.flush()

            # 6. Clear cart
            await session.execute(
                delete(CartItem).where(CartItem.user_id == user_id)
            )

            # 7. Commit savepoint
            await savepoint.commit()

            # Reload order with items for the response
            return await self._build_order_response(session, order.id)

        except Exception:
            await savepoint.rollback()
            raise

    async def get_orders(
        self, session: AsyncSession, user_id: UUID
    ) -> list[OrderResponse]:
        """Return all orders for the authenticated user, newest first."""
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        result = await session.execute(stmt)
        orders = result.unique().scalars().all()

        return [
            self._order_to_response(o) for o in orders
        ]

    async def get_order(
        self, session: AsyncSession, user_id: UUID, order_id: UUID
    ) -> OrderResponse:
        """Return full order detail. Owner or admin only (caller enforces)."""
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(selectinload(Order.items))
        )
        result = await session.execute(stmt)
        order = result.unique().scalar_one_or_none()

        if order is None:
            raise ValueError("Order not found")

        return self._order_to_response(order)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_cart_with_products(
        self, session: AsyncSession, user_id: UUID
    ) -> list[CartItem]:
        """Load cart items with product translations for snapshot building."""
        stmt = (
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(
                selectinload(CartItem.product).selectinload(
                    Product.translations
                ),
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def _process_checkout_items(
        self, session: AsyncSession, cart_items: list[CartItem]
    ) -> tuple[Decimal, list[dict]]:
        """Validate stock atomically and build order items data.

        Returns:
            (total, list of order_item_dicts)

        Raises:
            StockInsufficientError: if any product has insufficient stock
        """
        total = Decimal("0")
        order_items_data: list[dict] = []

        for item in cart_items:
            # Atomic stock deduction: UPDATE WHERE stock >= qty
            update_result = await session.execute(
                update(Product)
                .where(
                    Product.id == item.product_id,
                    Product.stock >= item.quantity,
                    Product.deleted_at.is_(None),
                )
                .values(stock=Product.stock - item.quantity)
                .returning(Product.id)
            )
            if update_result.scalar_one_or_none() is None:
                raise StockInsufficientError(
                    f"Insufficient stock for product {item.product_id}"
                )

            # Build snapshot from the product relationship (already loaded)
            product: Product = item.product
            snapshot = self._build_product_snapshot(product)
            price = product.price
            item_total = price * item.quantity
            total += item_total

            order_items_data.append({
                "product_id": item.product_id,
                "product_snapshot": snapshot,
                "quantity": item.quantity,
                "price": price,
            })

        return total, order_items_data

    @staticmethod
    def _build_product_snapshot(product: Product) -> dict:
        """Capture current product state as a JSONB snapshot.

        Freezes the checkout-time product name (from translations),
        price, size, and the product ID for future reference.
        """
        translations: list[ProductTranslation] = product.translations  # type: ignore[assignment]
        name = "Unknown product"
        if translations:
            # Prefer Spanish, then English, then first available
            for t in translations:
                if t.language_code == "es":
                    name = t.name
                    break
            else:
                for t in translations:
                    if t.language_code == "en":
                        name = t.name
                        break
                else:
                    name = translations[0].name

        return {
            "name": name,
            "price": str(product.price),
            "size": product.size.value if product.size else None,
            "product_id": str(product.id),
        }

    async def _build_order_response(
        self, session: AsyncSession, order_id: UUID
    ) -> OrderResponse:
        """Reload an order with its items and convert to a response DTO."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        result = await session.execute(stmt)
        order = result.unique().scalar_one()
        return self._order_to_response(order)

    @staticmethod
    def _order_to_response(order: Order) -> OrderResponse:
        """Convert an Order ORM instance with items to an OrderResponse."""
        items = [
            OrderItemResponse(
                id=oi.id,
                product_id=oi.product_id,
                product_snapshot=oi.product_snapshot,
                quantity=oi.quantity,
                price=oi.price,
            )
            for oi in order.items
        ]
        return OrderResponse(
            id=order.id,
            status=order.status.value,
            total=order.total,
            shipping_address=order.shipping_address,
            items=items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
