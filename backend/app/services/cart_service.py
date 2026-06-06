"""CartService — business logic for shopping cart CRUD.

Async methods accept SQLAlchemy AsyncSession injection at call time.
All operations are scoped to a single user via ``user_id``.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.product import Product, ProductTranslation
from app.schemas.cart import (
    AddToCartRequest,
    CartItemResponse,
    CartResponse,
    UpdateCartItemRequest,
)

logger = logging.getLogger(__name__)


class CartService:
    """Encapsulates all shopping cart business logic."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_cart(
        self, session: AsyncSession, user_id: UUID
    ) -> CartResponse:
        """Return the authenticated user's cart with line-item subtotals.

        Cart items are eager-loaded with product translations so the
        response can include a resolved product name per item.
        """
        cart_items = await self._load_cart_items(session, user_id)

        items = [self._build_cart_item_response(ci) for ci in cart_items]
        subtotal = sum(item.subtotal for item in items)

        return CartResponse(items=items, subtotal=subtotal)

    async def add_item(
        self, session: AsyncSession, user_id: UUID, data: AddToCartRequest
    ) -> CartResponse:
        """Add a product to the cart (or increment quantity if already present).

        Unit price is snapped from the products table at add-time.
        """
        # Check if item already exists for this user+product
        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == data.product_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Merge: increment quantity, keep existing unit_price
            existing.quantity += data.quantity
            await session.flush()
        else:
            # Fetch current product price
            product = await session.get(Product, data.product_id)
            if product is None:
                raise ValueError(f"Product {data.product_id} not found")

            cart_item = CartItem(
                user_id=user_id,
                product_id=data.product_id,
                quantity=data.quantity,
                unit_price=product.price,
            )
            session.add(cart_item)
            await session.flush()

        return await self.get_cart(session, user_id)

    async def update_quantity(
        self,
        session: AsyncSession,
        user_id: UUID,
        item_id: UUID,
        data: UpdateCartItemRequest,
    ) -> CartResponse:
        """Update the quantity of a cart item. Setting quantity to 0 removes it."""
        cart_item = await self._get_own_item(session, user_id, item_id)

        if data.quantity == 0:
            await session.delete(cart_item)
            await session.flush()
        else:
            cart_item.quantity = data.quantity
            await session.flush()

        return await self.get_cart(session, user_id)

    async def remove_item(
        self, session: AsyncSession, user_id: UUID, item_id: UUID
    ) -> CartResponse:
        """Remove a specific item from the user's cart."""
        cart_item = await self._get_own_item(session, user_id, item_id)
        await session.delete(cart_item)
        await session.flush()

        return await self.get_cart(session, user_id)

    async def clear_cart(
        self, session: AsyncSession, user_id: UUID
    ) -> CartResponse:
        """Remove all items from the user's cart in one operation."""
        await session.execute(
            delete(CartItem).where(CartItem.user_id == user_id)
        )
        await session.flush()

        return CartResponse(items=[], subtotal=Decimal("0"))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_cart_items(
        self, session: AsyncSession, user_id: UUID
    ) -> list[CartItem]:
        """Load all cart items for a user with eager-loaded product translations."""
        stmt = (
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(
                selectinload(CartItem.product).selectinload(
                    Product.translations
                ),
            )
            .order_by(CartItem.added_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def _get_own_item(
        self, session: AsyncSession, user_id: UUID, item_id: UUID
    ) -> CartItem:
        """Fetch a cart item by ID, ensuring it belongs to *user_id*.

        Raises ``ValueError`` if not found (controller maps to 404).
        """
        stmt = select(CartItem).where(
            CartItem.id == item_id,
            CartItem.user_id == user_id,
        )
        result = await session.execute(stmt)
        cart_item = result.scalar_one_or_none()
        if cart_item is None:
            raise ValueError("Cart item not found")
        return cart_item

    @staticmethod
    def _resolve_product_name(product: Product) -> str:
        """Extract the best available name from product translations.

        Prefers Spanish (default locale), falls back to English or the
        first available translation.
        """
        translations: list[ProductTranslation] = product.translations  # type: ignore[assignment]
        if not translations:
            return "Unknown product"

        for t in translations:
            if t.language_code == "es":
                return t.name
        for t in translations:
            if t.language_code == "en":
                return t.name
        return translations[0].name

    @classmethod
    def _build_cart_item_response(cls, cart_item: CartItem) -> CartItemResponse:
        """Convert a CartItem ORM instance to a response DTO."""
        product_name = cls._resolve_product_name(cart_item.product)
        subtotal = cart_item.unit_price * cart_item.quantity

        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=product_name,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            subtotal=subtotal,
            added_at=cart_item.added_at,
        )
