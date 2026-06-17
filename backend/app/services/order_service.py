"""OrderService — checkout and order history business logic.

Checkout creates an order + Stripe Checkout session atomically.
Stock is deducted at webhook time (``finalize_payment``), not at checkout.
Data access is delegated to ``OrderRepository`` — the service only
handles business logic (checkout orchestration, Stripe integration,
stock deduction, promotion consumption).
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductTranslation
from app.models.product_variant import ProductVariant
from app.repositories.order_repository import OrderRepository
from app.core.event_bus import event_bus
from app.core.events import OrderConfirmationEvent
from app.schemas.order import (
    CheckoutRequest,
    CheckoutResponse,
    OrderItemResponse,
    OrderResponse,
)
from app.exceptions import StripeError, StockInsufficientError

logger = logging.getLogger(__name__)


class CartEmptyError(ValueError):
    """Raised when attempting checkout with an empty cart."""


class OrderService:
    """Encapsulates checkout and order history business logic.

    Injects ``OrderRepository`` for data access.  If no repository is
    provided, a default instance is created (backward-compatible).
    """

    def __init__(self, order_repo: OrderRepository | None = None) -> None:
        self._repo = order_repo or OrderRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def checkout(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
        customer_email: str | None,
        guest_email: str | None,
        shipping_address: dict,
    ) -> CheckoutResponse:
        """Convert the cart into an order and create a Stripe session.

        Dual-scope: supports authenticated users (``user_id``) and guest
        sessions (``session_id``). Exactly one scope must be provided.

        Flow:
        1. Load cart items by scope (user_id or session_id)
        2. Validate cart is not empty
        3. Begin nested transaction (savepoint)
        4. Build order items data (stock is NOT deducted — deferred to webhook)
        5. Create Order + OrderItems with product snapshots
           (sets ``user_id`` for users, ``guest_email`` for guests)
        6. Clear cart by scope
        7. Create Stripe Checkout session (guest-aware success_url)
        8. Commit savepoint

        Stock deduction happens later in ``finalize_payment()``, called by
        the Stripe webhook handler upon ``checkout.session.completed``.

        Raises:
            ValueError: if neither or both scope identifiers are provided
            CartEmptyError: cart has no items → 400
            StripeError: Stripe API call fails → 502 (rolls back entire order)
        """
        # Validate scope XOR
        has_user = user_id is not None
        has_session = session_id is not None
        if has_user == has_session:
            raise ValueError(
                "Exactly one of user_id or session_id must be provided"
            )
        is_guest = has_session

        # 1. Load cart items with product translations for snapshots
        cart_items = await self._load_cart_with_products(
            session, user_id, session_id
        )

        # 2. Validate
        if not cart_items:
            raise CartEmptyError("Cart is empty")

        # 3. Begin savepoint
        savepoint = await session.begin_nested()
        try:
            # 4. Build order item data (NO stock deduction)
            total, order_items_data = await self._build_order_items(
                session, cart_items
            )

            # 5. Create order — set user_id for users, guest_email for guests
            order = Order(
                user_id=user_id,
                guest_email=guest_email if is_guest else None,
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

            # 6. Clear cart by scope
            if user_id is not None:
                await session.execute(
                    delete(CartItem).where(CartItem.user_id == user_id)
                )
            else:
                await session.execute(
                    delete(CartItem).where(CartItem.session_id == session_id)
                )

            # 7. Create Stripe checkout session (guest-aware)
            from app.services.stripe_service import StripeService

            stripe_svc = StripeService()
            checkout_url = await stripe_svc.create_checkout_session(
                session,
                order,
                cart_items,
                user_email=customer_email,
                user_id=user_id,
                is_guest=is_guest,
            )

            # 8. Commit savepoint
            await savepoint.commit()

            logger.info(
                "Checkout complete — order %s for %s",
                order.id,
                f"user {user_id}" if not is_guest else f"guest session {session_id}",
            )
            return CheckoutResponse(
                checkout_url=checkout_url, order_id=order.id
            )

        except (StripeError, Exception):
            await savepoint.rollback()
            raise

    async def get_orders(
        self, session: AsyncSession, user_id: UUID
    ) -> list[OrderResponse]:
        """Return all orders for the authenticated user, newest first."""
        orders = await self._repo.get_by_user(session, user_id)
        return [self._order_to_response(o) for o in orders]

    async def get_order(
        self, session: AsyncSession, user_id: UUID, order_id: UUID
    ) -> OrderResponse:
        """Return full order detail. Owner or admin only (caller enforces)."""
        order = await self._repo.get_with_items_by_user(
            session, order_id, user_id
        )
        if order is None:
            raise ValueError("Order not found")
        return self._order_to_response(order)

    # ------------------------------------------------------------------
    # Payment finalization (called from Stripe webhook)
    # ------------------------------------------------------------------

    async def finalize_payment(
        self, session: AsyncSession, order: Order
    ) -> None:
        """Deduct stock, increment promotion usage, confirm order, and send email.

        Called by the Stripe webhook handler when
        ``checkout.session.completed`` is received.

        Promotions are consumed at this point — ``current_uses`` is
        incremented for every order item that was purchased under a
        promotion.  This is the correct semantic (count actual purchases,
        not cart views).

        **Atomicity**: ALL mutations (promotion usage + stock deduction +
        status transition) happen inside a savepoint.  Stock is pre-validated
        BEFORE any mutation to avoid partial deductions.  If any step fails,
        the entire savepoint is rolled back.

        Email is sent OUTSIDE the savepoint — failures are logged but do not
        affect the transaction.

        Raises:
            StockInsufficientError: if any variant lacks sufficient stock.
        """
        from app.models.promotion import Promotion as _Promotion

        # Reload order items to ensure they are attached to the session
        await session.refresh(order, ["items"])

        # STEP 1: Pre-validate ALL stock before any mutation
        for item in order.items:
            variant_id_str = item.product_snapshot.get("variant_id")
            if variant_id_str is None:
                continue  # Product has no variants — nothing to validate
            try:
                variant_id = UUID(variant_id_str)
            except (ValueError, TypeError):
                logger.warning(
                    "Invalid variant_id %r in order_item %s product_snapshot",
                    variant_id_str,
                    item.id,
                )
                continue

            result = await session.execute(
                select(ProductVariant.stock).where(
                    ProductVariant.id == variant_id,
                    ProductVariant.deleted_at.is_(None),
                )
            )
            stock_row = result.scalar_one_or_none()
            if stock_row is None or stock_row < item.quantity:
                raise StockInsufficientError(
                    f"Insufficient stock for variant {variant_id} "
                    f"(order_item {item.id}, requested {item.quantity})"
                )

        # STEP 2: Wrap ALL mutations in a savepoint for atomicity
        savepoint = await session.begin_nested()
        try:
            # Increment promotion usage — atomic conditional UPDATE
            for item in order.items:
                promo_code = item.product_snapshot.get("promotion_code")
                if promo_code:
                    result = await session.execute(
                        update(_Promotion)
                        .where(_Promotion.code == promo_code)
                        .where(
                            _Promotion.max_uses.is_(None)
                            | (_Promotion.current_uses < _Promotion.max_uses)
                        )
                        .values(current_uses=_Promotion.current_uses + 1)
                        .returning(_Promotion.id)
                    )
                    if not result.scalar_one_or_none():
                        raise StockInsufficientError(
                            f"Promotion {promo_code} usage cap reached"
                        )

            # Deduct stock for each order item (atomic conditional UPDATE)
            for item in order.items:
                await self._deduct_stock_for_item(session, item)

            # Transition order to confirmed
            order.status = OrderStatus.CONFIRMED
            await session.flush()

            await savepoint.commit()

        except Exception:
            await savepoint.rollback()
            raise

        # Emit confirmation event via event bus (fire-and-forget)
        if order.user_id is not None:
            event_bus.emit(OrderConfirmationEvent(
                user_id=order.user_id,
                order_id=order.id,
            ))
        else:
            logger.info(
                "Skipping confirmation email for guest order %s", order.id
            )

        logger.info(
            "Order %s finalized — stock deducted, status confirmed", order.id
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_cart_with_products(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
    ) -> list[CartItem]:
        """Load cart items with product translations and variant for snapshot building.

        Scopes to either ``user_id`` (authenticated) or ``session_id`` (guest).
        Exactly one scope identifier must be provided.
        """
        if user_id is not None:
            scope = CartItem.user_id == user_id
        else:
            scope = CartItem.session_id == session_id

        stmt = (
            select(CartItem)
            .where(scope)
            .options(
                selectinload(CartItem.product).selectinload(
                    Product.translations
                ),
                selectinload(CartItem.variant),
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def _build_order_items(
        self, session: AsyncSession, cart_items: list[CartItem]
    ) -> tuple[Decimal, list[dict]]:
        """Build order item data from cart items WITHOUT deducting stock.

        Stock deduction is deferred to ``finalize_payment()`` at webhook time.
        Product snapshots are captured at checkout time for order history.
        Active promotion codes are resolved and stored in the snapshot so
        ``finalize_payment()`` can increment ``current_uses``.

        Returns:
            (total, list of order_item_dicts)
        """
        from app.services.promotion_service import PromotionService

        promo_service = PromotionService()
        product_ids = list({ci.product_id for ci in cart_items})
        promotions = await promo_service.get_active_promotions_for_products(
            session, product_ids
        )

        total = Decimal("0")
        order_items_data: list[dict] = []

        for item in cart_items:
            promo = promotions.get(item.product_id)
            promo_code = promo.code if promo else None
            snapshot = self._build_product_snapshot(item, promo_code=promo_code)
            price = item.unit_price
            item_total = price * item.quantity
            total += item_total

            order_items_data.append({
                "product_id": item.product_id,
                "product_snapshot": snapshot,
                "quantity": item.quantity,
                "price": price,
            })

        return total, order_items_data

    async def _deduct_stock_for_item(
        self, session: AsyncSession, item: OrderItem
    ) -> None:
        """Atomically deduct stock for a single order item's variant.

        Uses a conditional UPDATE with a stock >= quantity guard to prevent
        negative stock from race conditions.

        Raises:
            StockInsufficientError: if the variant has insufficient stock or
                was deleted between checkout and payment.
        """
        variant_id_str = item.product_snapshot.get("variant_id")
        if variant_id_str is None:
            return  # Product has no variants — nothing to deduct

        try:
            variant_id = UUID(variant_id_str)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid variant_id %r in order_item %s product_snapshot",
                variant_id_str,
                item.id,
            )
            return

        result = await session.execute(
            update(ProductVariant)
            .where(
                ProductVariant.id == variant_id,
                ProductVariant.stock >= item.quantity,
                ProductVariant.deleted_at.is_(None),
            )
            .values(stock=ProductVariant.stock - item.quantity)
            .returning(ProductVariant.id)
        )

        if result.scalar_one_or_none() is None:
            raise StockInsufficientError(
                f"Insufficient stock for variant {variant_id} "
                f"(order_item {item.id}, requested {item.quantity})"
            )

    @staticmethod
    def _build_product_snapshot(
        cart_item: CartItem,
        promo_code: str | None = None,
    ) -> dict:
        """Capture current product + variant state as a JSONB snapshot.

        Freezes the checkout-time product name, price, variant info
        (id, size, color, SKU), and product ID for future reference.
        When a promotion is active for the product, its code is also
        stored so ``finalize_payment()`` can increment ``current_uses``.
        """
        product: Product = cart_item.product
        translations: list[ProductTranslation] = product.translations  # type: ignore[assignment]
        name = "Unknown product"
        if translations:
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

        variant: ProductVariant | None = cart_item.variant
        size_str = None
        color_str = None
        sku_str = None
        if variant is not None:
            size_str = variant.size.value if variant.size else None
            color_str = variant.color
            sku_str = variant.sku

        snapshot = {
            "name": name,
            "price": str(product.price),
            "size": size_str,
            "color": color_str,
            "sku": sku_str,
            "product_id": str(product.id),
            "variant_id": str(variant.id) if variant else None,
        }
        if promo_code:
            snapshot["promotion_code"] = promo_code
        return snapshot

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
            payment_status=order.payment_status.value,
            stripe_session_id=order.stripe_session_id,
            total=order.total,
            shipping_address=order.shipping_address,
            items=items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


