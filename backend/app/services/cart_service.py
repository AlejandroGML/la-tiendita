"""CartService — business logic for shopping cart CRUD.

Async methods accept SQLAlchemy AsyncSession injection at call time.
All operations are dual-scope: scoped to either a registered user
(``user_id``) or an anonymous guest session (``session_id``).
Exactly one scope identifier must be provided (XOR).
"""

import logging
import re
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ColumnElement, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.product import Product, ProductTranslation
from app.models.product_variant import ProductVariant
from app.repositories.cart_repository import CartRepository
from app.repositories.variant_repository import VariantRepository
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

    def __init__(
        self,
        promotion_service=None,
        cart_repo: CartRepository | None = None,
        variant_repo: VariantRepository | None = None,
    ):
        """Optionally inject a PromotionService; creates a local default if omitted."""
        if promotion_service is None:
            from app.services.promotion_service import PromotionService

            promotion_service = PromotionService()
        self._promotion_service = promotion_service
        self._cart_repo = cart_repo or CartRepository()
        self._variant_repo = variant_repo or VariantRepository()

    # ------------------------------------------------------------------
    # Scope helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_scope(
        user_id: UUID | None, session_id: UUID | None
    ) -> None:
        """Validate exactly one scope identifier is provided (XOR)."""
        has_user = user_id is not None
        has_session = session_id is not None
        if has_user == has_session:
            raise ValueError(
                "Exactly one of user_id or session_id must be provided"
            )

    @staticmethod
    def _scope_filter(
        user_id: UUID | None, session_id: UUID | None,
    ) -> ColumnElement[bool]:
        """Return a SQLAlchemy WHERE filter clause for the active scope.

        Exactly one of *user_id* or *session_id* must be non-None.
        """
        CartService._validate_scope(user_id, session_id)
        if user_id is not None:
            return CartItem.user_id == user_id
        return CartItem.session_id == session_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_cart(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
    ) -> CartResponse:
        """Return a cart with line-item subtotals, scoped to user or session.

        Cart items are eager-loaded with product translations so the
        response can include a resolved product name per item.
        Active promotions are resolved in batch and applied to items,
        producing sale pricing, savings, and original-subtotal aggregates.
        """
        cart_items = await self._load_cart_items(session, user_id, session_id)

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
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
        data: AddToCartRequest,
    ) -> CartResponse:
        """Add a product to the cart (or increment quantity if already present).

        Scoped by *user_id* OR *session_id* (XOR). The unique lookup
        uses the correct partial unique index depending on scope.

        When ``variant_id`` is provided:
          - Validates the variant exists, belongs to the product, and has
            stock >= 1 before allowing add-to-cart.

        When ``variant_id`` is None:
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
            session, user_id, session_id, data.product_id, data.variant_id
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
                session_id=session_id,
                product_id=data.product_id,
                variant_id=data.variant_id,
                size=variant.size.value if (variant and variant.size) else None,
                color=variant.color if variant else None,
                quantity=data.quantity,
                unit_price=product.price,
            )
            session.add(cart_item)
            await session.flush()

        return await self.get_cart(session, user_id, session_id)

    async def update_quantity(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
        item_id: UUID,
        data: UpdateCartItemRequest,
    ) -> CartResponse:
        """Update the quantity of a cart item scoped to user or session.

        Setting quantity to 0 removes it. Validates variant stock for the
        new quantity when variant_id is set.
        """
        cart_item = await self._get_own_item(
            session, user_id, session_id, item_id
        )

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

        return await self.get_cart(session, user_id, session_id)

    async def remove_item(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
        item_id: UUID,
    ) -> CartResponse:
        """Remove a specific item from a user or session cart."""
        cart_item = await self._get_own_item(
            session, user_id, session_id, item_id
        )
        await session.delete(cart_item)
        await session.flush()

        return await self.get_cart(session, user_id, session_id)

    async def clear_cart(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
    ) -> CartResponse:
        """Remove all items from a user or session cart in one operation."""
        await self._cart_repo.clear_scope(
            session, user_id=user_id, session_id=session_id
        )

        return CartResponse(items=[], subtotal=Decimal("0"))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_cart_items(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
    ) -> list[CartItem]:
        """Load all cart items scoped to user or session.

        Eager-loads product translations and variant for response building.
        """
        return await self._cart_repo.get_items(
            session, user_id=user_id, session_id=session_id
        )

    async def _get_own_item(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
        item_id: UUID,
    ) -> CartItem:
        """Fetch a cart item by ID, scoped to user or session.

        Raises ``ValueError`` if not found (controller maps to 404).
        """
        cart_item = await self._cart_repo.get_own_item(
            session, item_id, user_id=user_id, session_id=session_id
        )
        if cart_item is None:
            raise ValueError("Cart item not found")
        return cart_item

    @staticmethod
    @staticmethod
    def _resolve_product_name(product: Product) -> str:
        """Extract the best available name from product translations.

        Prefers Spanish (default locale), falls back to English or the
        first available translation.  If no translations exist, formats
        the slug as a readable name (e.g. ``odd-molly-top`` → ``Odd Molly Top``).
        """
        translations: list[ProductTranslation] = product.translations  # type: ignore[assignment]
        if translations:
            for t in translations:
                if t.language_code == "es" and t.name:
                    return t.name
            for t in translations:
                if t.language_code == "en" and t.name:
                    return t.name
            return translations[0].name
        # Fallback: format slug as readable name
        slug = product.slug or ""
        if not slug:
            return "Producto"
        cleaned = re.sub(r"[-\s][a-z0-9]{4,8}$", "", slug)
        return " ".join(w.capitalize() for w in cleaned.split("-"))

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

        image_url = None
        product_slug = cart_item.product.slug if cart_item.product else None
        if cart_item.product and cart_item.product.image_urls:
            urls = cart_item.product.image_urls
            if isinstance(urls, list) and len(urls) > 0:
                image_url = str(urls[0])

        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=product_name,
            product_slug=product_slug,
            image_url=image_url,
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

    async def _find_existing_item(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        session_id: UUID | None,
        product_id: UUID,
        variant_id: UUID | None,
    ) -> CartItem | None:
        """Find an existing cart item matching the scope + partial unique index.

        Uses the correct unique index depending on scope (user or session)
        and whether a variant is specified.
        """
        return await self._cart_repo.find_existing(
            session,
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            variant_id=variant_id,
        )

    async def _get_default_variant(
        self, session: AsyncSession, product_id: UUID
    ) -> ProductVariant | None:
        """Return the first non-deleted variant for a product (or None)."""
        variants = await self._variant_repo.get_by_product(session, product_id)
        return variants[0] if variants else None
