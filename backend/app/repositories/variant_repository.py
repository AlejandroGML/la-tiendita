"""VariantRepository — encapsulates ProductVariant data access.

Extracts all SQLAlchemy query construction from ``VariantService`` into a
dedicated repository.  The service retains SKU generation, cart-reference
validation, and variant CRUD orchestration.
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_variant import ProductVariant
from app.repositories.base import BaseRepository


class VariantRepository(BaseRepository[ProductVariant]):
    """ProductVariant-specific data access — product-scoped lookups, stock.

    Usage::

        repo = VariantRepository()
        variants = await repo.get_by_product(session, product_id)
        variant = await repo.get_by_sku(session, "CHA-L-04")
    """

    def __init__(self) -> None:
        super().__init__(ProductVariant)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_by_product(
        self,
        session: AsyncSession,
        product_id: UUID,
    ) -> list[ProductVariant]:
        """Return all non-deleted variants for a product, ordered by creation.

        Args:
            session: Active async DB session.
            product_id: The product UUID.

        Returns:
            List of variants (empty if none exist).
        """
        result = await session.execute(
            select(ProductVariant)
            .where(
                ProductVariant.product_id == product_id,
                ProductVariant.deleted_at.is_(None),
            )
            .order_by(ProductVariant.created_at)
        )
        return list(result.scalars().all())

    async def get_by_sku(
        self,
        session: AsyncSession,
        sku: str,
    ) -> ProductVariant | None:
        """Fetch a variant by its unique SKU.

        Args:
            session: Active async DB session.
            sku: The variant SKU to look up.

        Returns:
            The variant or ``None``.
        """
        return await self.find_one(session, ProductVariant.sku == sku)

    async def get_active_for_product(
        self,
        session: AsyncSession,
        product_id: UUID,
    ) -> list[ProductVariant]:
        """Return non-deleted variants with stock > 0 for a product.

        Used by the order flow to determine available options.

        Args:
            session: Active async DB session.
            product_id: The product UUID.

        Returns:
            List of in-stock variants.
        """
        return await self.find_all(
            session,
            ProductVariant.product_id == product_id,
            ProductVariant.deleted_at.is_(None),
            ProductVariant.stock > 0,
        )

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    async def deduct_stock(
        self,
        session: AsyncSession,
        variant_id: UUID,
        qty: int,
    ) -> bool:
        """Atomically deduct stock + reserved stock if sufficient (TOCTOU-safe).

        Uses a conditional ``UPDATE ... RETURNING`` — stock and reserved_stock
        are only decremented when ``stock >= qty`` and the variant is not
        deleted.  Concurrent checkouts cannot oversell.

        Args:
            session: Active async DB session.
            variant_id: The variant UUID.
            qty: Quantity to deduct (must be >= 1).

        Returns:
            ``True`` if the deduction succeeded, ``False`` if stock was
            insufficient or the variant was deleted.
        """
        result = await session.execute(
            update(ProductVariant)
            .where(
                ProductVariant.id == variant_id,
                ProductVariant.stock >= qty,
                ProductVariant.deleted_at.is_(None),
            )
            .values(
                stock=ProductVariant.stock - qty,
                reserved_stock=ProductVariant.reserved_stock - qty,
            )
            .returning(ProductVariant.id)
        )
        return result.scalar_one_or_none() is not None
