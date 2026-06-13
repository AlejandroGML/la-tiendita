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
from app.models.product_variant import ProductVariant
from app.schemas.cart import (
    AddToCartRequest,
    CartItemResponse,
    CartResponse,
    UpdateCartItemRequest,
)

logger = logging.getLogger(__name__)


class StockInsufficientError(ValueError):
    """Raised when variant stock is insufficient for the requested quantity."""


class CartService:
    """Encapsulates all shopping cart business logic."""

    def __init__(self, promotion_service=None):
        """Optionally inject a PromotionService; creates a local default if omitted."""
        if promotion_service is None:
            from app.services.promotion_service import PromotionService

            promotion_service = PromotionService()
        self._promotion_service = promotion_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_cart(
        self, session: AsyncSession, user_id: UUID
    ) -> CartResponse:
        """Return the authenticated user's cart with line-item subtotals.

        Cart items are eager-loaded with product translations so the
        response can include a resolved product name per item.
        Active promotions are resolved in batch and applied to items,
        producing sale pricing, savings, and original-subtotal aggregates.
        """
        cart_items = await self._load_cart_items(session, user_id)

        # Resolve active promotions for all cart item products
        product_ids = list({ci.product_id for ci in cart_items})
        promotions = await self._promotion_service.get_active_promotions_for_products(
            session, product_ids
        )

        items = [self._build_cart_item_response(ci, promotions) for ci in cart_items]
        subtotal = sum(item.subtotal for item in items)

        # Compute cart-level discount aggregates
        original_subtotal_val = Decimal("0")
        total_savings_val = Decimal("0")
        has_any_discount = False

        for item in items:
            if item.original_unit_price is not None:
                has_any_discount = True
                original_subtotal_val += Decimal(item.original_unit_price) * item.quantity
            else:
                original_subtotal_val += item.subtotal
            if item.savings is not None:
                total_savings_val += Decimal(item.savings)

        return CartResponse(
            items=items,
            subtotal=subtotal,
            original_subtotal=str(original_subtotal_val) if has_any_discount else None,
            total_savings=str(total_savings_val) if has_any_discount else None,
        )

    async def add_item(
        self, session: AsyncSession, user_id: UUID, data: AddToCartRequest
    ) -> CartResponse:
        """Add a product to the cart (or increment quantity if already present).

        When ``variant_id`` is provided:
          - Validates the variant exists, belongs to the product, and has
            stock >= 1 before allowing add-to-cart.
          - Merges on the partial unique index ``(user_id, variant_id)``.

        When ``variant_id`` is None:
          - Merges on the partial unique index ``(user_id, product_id)``.
          - Falls back to the first non-deleted variant's stock for
            validation if the product has variants.

        Unit price is snapped from the products table at add-time.
        """
        # Validate variant if provided
        variant: ProductVariant | None = None
        if data.variant_id is not None:
            variant = await session.get(ProductVariant, data.variant_id)
            if variant is None or variant.deleted_at is not None:
                raise ValueError("variant not available")
            if variant.product_id != data.product_id:
                raise ValueError("variant does not belong to product")
            if variant.stock < 1:
                raise StockInsufficientError(
                    f"Variant {data.variant_id} is out of stock"
                )
        else:
            # Fallback: check any variant stock for the product
            variant = await self._get_default_variant(session, data.product_id)
            if variant is not None and variant.stock < 1:
                raise StockInsufficientError(
                    f"Product {data.product_id} is out of stock"
                )

        # Check if item already exists (handled by partial unique indexes)
        existing = await self._find_existing_item(
            session, user_id, data.product_id, data.variant_id
        )

        if existing is not None:
            # Merge: increment quantity — validate stock
            if variant is not None and variant.stock < existing.quantity + data.quantity:
                raise StockInsufficientError(
                    f"Only {variant.stock} in stock for variant {variant.id}"
                )
            existing.quantity += data.quantity
            await session.flush()
        else:
            # Fetch current product price
            product = await session.get(Product, data.product_id)
            if product is None or product.deleted_at is not None:
                raise ValueError("product not available")

            cart_item = CartItem(
                user_id=user_id,
                product_id=data.product_id,
                variant_id=data.variant_id,
                size=variant.size.value if (variant and variant.size) else None,
                color=variant.color if variant else None,
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
        """Update the quantity of a cart item. Setting quantity to 0 removes it.

        Validates variant stock for the new quantity when variant_id is set.
        """
        cart_item = await self._get_own_item(session, user_id, item_id)

        if data.quantity == 0:
            await session.delete(cart_item)
            await session.flush()
        else:
            # Validate variant stock if applicable
            if cart_item.variant_id is not None:
                variant = await session.get(ProductVariant, cart_item.variant_id)
                if variant is None or variant.deleted_at is not None:
                    raise ValueError("variant no longer available")
                if variant.stock < data.quantity:
                    raise StockInsufficientError(
                        f"Only {variant.stock} in stock for variant "
                        f"{cart_item.variant_id}"
                    )
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
        """Load all cart items for a user with eager-loaded product and variant."""
        stmt = (
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(
                selectinload(CartItem.product).selectinload(
                    Product.translations
                ),
                selectinload(CartItem.variant),
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

    def _build_cart_item_response(
        self,
        cart_item: CartItem,
        promotions: dict | None = None,
    ) -> CartItemResponse:
        """Convert a CartItem ORM instance to a response DTO.

        When *promotions* includes an active promotion for the item's
        product, computes sale pricing relative to the snapshotted
        ``unit_price`` and attaches ``original_unit_price`` and
        ``savings``.  Otherwise these fields remain ``None``.
        The frontend derives discount labels from ``discount_percent``.
        """
        product_name = self._resolve_product_name(cart_item.product)
        unit_price = cart_item.unit_price
        subtotal = unit_price * cart_item.quantity
        original_unit_price = None
        discount_label = None
        savings = None

        if promotions and cart_item.product_id in promotions:
            promo = promotions[cart_item.product_id]
            # Sale price relative to the snapshotted unit_price
            sale_price = round(
                float(unit_price) * (1 - promo.discount_percent / 100), 2
            )
            original_unit_price = str(unit_price)
            savings_amount = (float(unit_price) - sale_price) * cart_item.quantity
            savings = str(round(savings_amount, 2))
            unit_price = Decimal(str(sale_price))
            subtotal = unit_price * cart_item.quantity

        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=product_name,
            quantity=cart_item.quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            variant_id=cart_item.variant_id,
            size=cart_item.size,
            color=cart_item.color,
            added_at=cart_item.added_at,
            original_unit_price=original_unit_price,
            discount_label=discount_label,
            savings=savings,
        )

    @staticmethod
    async def _find_existing_item(
        session: AsyncSession,
        user_id: UUID,
        product_id: UUID,
        variant_id: UUID | None,
    ) -> CartItem | None:
        """Find an existing cart item matching the partial unique index.

        When ``variant_id`` is provided, matches on ``(user_id, variant_id)``.
        When ``variant_id`` is None, matches on ``(user_id, product_id)``
        with ``variant_id IS NULL``.
        """
        if variant_id is not None:
            stmt = select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.variant_id == variant_id,
            )
        else:
            stmt = select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
                CartItem.variant_id.is_(None),
            )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_default_variant(
        session: AsyncSession, product_id: UUID
    ) -> ProductVariant | None:
        """Return the first non-deleted variant for a product (or None)."""
        from sqlalchemy import select as _select

        stmt = (
            _select(ProductVariant)
            .where(
                ProductVariant.product_id == product_id,
                ProductVariant.deleted_at.is_(None),
            )
            .order_by(ProductVariant.created_at)
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
