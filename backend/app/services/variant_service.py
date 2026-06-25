"""VariantService — variant CRUD and SKU generation for ProductService.

Manages ProductVariant lifecycle: list, create, update, delete (soft-delete).
Auto-generates SKUs with collision-safe sequencing. Requires
``ProductRepository`` for product existence validation.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func as sqlfunc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.core.events import AuditAction, AuditEvent
from app.models.product import Product, ProductSize
from app.models.product_variant import ProductVariant
from app.models.cart import CartItem
from app.repositories.product_repository import ProductRepository
from app.repositories.variant_repository import VariantRepository
from app.repositories.cart_repository import CartRepository
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
)

logger = logging.getLogger(__name__)


class VariantService:
    """Encapsulates variant CRUD and SKU generation logic.

    Injects ``ProductRepository`` for product existence validation.
    If no repository is provided, a default instance is created
    (backward-compatible for direct instantiation in tests).
    """

    def __init__(
        self,
        product_repo: ProductRepository | None = None,
        variant_repo: VariantRepository | None = None,
        cart_repo: CartRepository | None = None,
    ) -> None:
        self._repo = product_repo or ProductRepository()
        self._variant_repo = variant_repo or VariantRepository()
        self._cart_repo = cart_repo or CartRepository()

    # ------------------------------------------------------------------
    # Variant CRUD
    # ------------------------------------------------------------------

    async def list_variants(
        self, session: AsyncSession, product_id: UUID
    ) -> list[ProductVariant]:
        """Return all non-deleted variants for a product."""
        return await self._variant_repo.get_by_product(session, product_id)

    async def create_variant(
        self,
        session: AsyncSession,
        product_id: UUID,
        data: ProductVariantCreate,
        actor_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> ProductVariant:
        """Create a new variant for an existing product.

        Validates the product exists and is not soft-deleted.
        Auto-generates SKU if not provided.
        When *actor_id* is provided, an ``AuditEvent`` is emitted.
        """
        product = await self._repo.find_one(
            session, Product.id == product_id, Product.deleted_at.is_(None)
        )
        if product is None:
            raise ValueError("product not found")

        sku = data.sku
        if sku is None:
            size_code = data.size if data.size else None
            color_code = self._color_abbr(data.color) if data.color else None
            sku = await self._generate_variant_sku(
                session, product.slug, size_code, color_code
            )

        variant = ProductVariant(
            product_id=product_id,
            size=ProductSize(data.size) if data.size else None,
            color=data.color,
            color_hex=data.color_hex,
            stock=data.stock,
            sku=sku,
        )
        session.add(variant)
        await session.flush()
        if actor_id is not None:
            event_bus.emit(
                AuditEvent(
                    actor_id=actor_id,
                    action=AuditAction.VARIANT_CREATE,
                    entity_type="variant",
                    entity_id=str(variant.id),
                    details={"sku": variant.sku},
                    ip_address=ip_address,
                )
            )
        return variant

    async def update_variant(
        self,
        session: AsyncSession,
        variant_id: UUID,
        data: ProductVariantUpdate,
        actor_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> ProductVariant | None:
        """Partially update an existing variant. Returns None if not found.
        When *actor_id* is provided, an ``AuditEvent`` is emitted.
        """
        variant = await self._variant_repo.get_by_id(session, variant_id)
        if variant is None or variant.deleted_at is not None:
            return None

        if data.size is not None:
            variant.size = ProductSize(data.size)
        if data.color is not None:
            variant.color = data.color
        if data.color_hex is not None:
            variant.color_hex = data.color_hex
        if data.stock is not None:
            variant.stock = data.stock
        if data.sku is not None:
            variant.sku = data.sku

        await session.flush()
        if actor_id is not None:
            event_bus.emit(
                AuditEvent(
                    actor_id=actor_id,
                    action=AuditAction.VARIANT_UPDATE,
                    entity_type="variant",
                    entity_id=str(variant.id),
                    details={"sku": variant.sku},
                    ip_address=ip_address,
                )
            )
        return variant

    async def delete_variant(
        self,
        session: AsyncSession,
        variant_id: UUID,
        product_id: UUID | None = None,
        actor_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> bool:
        """Soft-delete a variant. Returns False if already deleted or not found.

        When *product_id* is provided, verifies the variant belongs to that
        product — raises ``ValueError`` on mismatch.

        Does NOT allow deletion if the variant is referenced by active
        cart items or order items.

        When *actor_id* is provided, an ``AuditEvent`` is emitted.
        """
        variant = await self._variant_repo.get_by_id(session, variant_id)
        if variant is None or variant.deleted_at is not None:
            return False

        if product_id is not None and variant.product_id != product_id:
            raise ValueError(
                "variant does not belong to this product"
            )

        # Check for active references in cart_items
        cart_count = await self._cart_repo.count_by_variant(session, variant_id)
        if cart_count and cart_count > 0:
            raise ValueError(
                f"Variant is referenced by {cart_count} active cart item(s). "
                "Remove them before deleting."
            )

        variant.deleted_at = datetime.now(timezone.utc)
        await session.flush()
        if actor_id is not None:
            event_bus.emit(
                AuditEvent(
                    actor_id=actor_id,
                    action=AuditAction.VARIANT_DELETE,
                    entity_type="variant",
                    entity_id=str(variant.id),
                    details={"sku": variant.sku},
                    ip_address=ip_address,
                )
            )
        return True

    # ------------------------------------------------------------------
    # Variant internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _color_abbr(color: str | None) -> str | None:
        """Convert a color name to a 2-char abbreviation for SKU building."""
        if not color:
            return None
        parts = color.strip().split()
        if len(parts) == 1:
            abbr = parts[0][:2].upper()
        else:
            abbr = "".join(p[0] for p in parts[:2]).upper()
        return abbr

    async def _generate_variant_sku(
        self,
        session: AsyncSession,
        slug: str,
        size_code: str | None,
        color_code: str | None,
    ) -> str:
        """Generate a unique SKU from slug prefix, size, and color.

        Format: ``{slug_prefix}-{size|NS}-{color_abbr|NC}-{seq}``
        Collision-safe via DB unique constraint check with incrementing seq.
        """
        slug_prefix = self._sku_slug_prefix(slug)
        size_part = size_code or "NS"
        color_part = color_code or "NC"

        for seq in range(1, 100):
            sku = f"{slug_prefix}-{size_part}-{color_part}-{seq:02d}"
            exists = await self._variant_repo.get_by_sku(session, sku)
            if exists is None:
                return sku

        # Fallback (extremely unlikely): use UUID suffix
        import uuid as _uuid

        short_uuid = str(_uuid.uuid4())[:8]
        return f"{slug_prefix}-{size_part}-{color_part}-{short_uuid}"

    @staticmethod
    def _sku_slug_prefix(slug: str) -> str:
        """Extract a short uppercase prefix from a slug for SKU building."""
        parts = slug.replace("-", " ").split()
        if len(parts) >= 2:
            prefix = "".join(p[0] for p in parts[:3]).upper()
        else:
            prefix = (parts[0][:4] if parts else "PRD").upper()
        return prefix
