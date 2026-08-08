"""PromotionRepository — encapsulates Promotion data access.

Extracts all SQLAlchemy queries from ``PromotionService`` into a dedicated
repository.  The service retains date-range validation, translation management,
and response DTO construction.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.promotion import Promotion
from app.repositories.base import BaseRepository


class PromotionRepository(BaseRepository[Promotion]):
    """Promotion-specific data access — active lookups, code search.

    Usage::

        repo = PromotionRepository()
        active = await repo.get_active(session, lang="es")
        promo = await repo.get_by_code(session, "DESC10")
    """

    def __init__(self) -> None:
        super().__init__(Promotion)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_active(
        self,
        session: AsyncSession,
        lang: str = "es",
    ) -> list[Promotion]:
        """Return all currently active promotions with translations.

        A promotion is active when ALL of these hold:
        - ``is_active = True``
        - ``start_date IS NULL OR start_date <= now()``
        - ``end_date IS NULL OR end_date >= now()``
        - ``max_uses IS NULL OR current_uses < max_uses``

        Results are ordered by most recent.

        Args:
            session: Active async DB session.
            lang: Language code hint (reserved — currently loads all
                  translations, return structure not filtered by lang).

        Returns:
            List of active promotions.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Promotion)
            .where(
                Promotion.is_active.is_(True),
                (Promotion.start_date.is_(None))
                | (Promotion.start_date <= now),
                (Promotion.end_date.is_(None))
                | (Promotion.end_date >= now),
                (Promotion.max_uses.is_(None))
                | (Promotion.current_uses < Promotion.max_uses),
            )
            .options(selectinload(Promotion.translations))
            .order_by(Promotion.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_by_code(
        self,
        session: AsyncSession,
        code: str,
    ) -> Promotion | None:
        """Fetch a promotion by its unique discount code.

        Args:
            session: Active async DB session.
            code: The promotion code.

        Returns:
            The promotion or ``None``.
        """
        return await self.find_one(session, Promotion.code == code)

    async def get_best_for_product(
        self,
        session: AsyncSession,
        product_id: UUID,
    ) -> Promotion | None:
        """Return the best active promotion for a product, if any.

        Matches both product-scoped promotions and store-wide promotions
        (``product_id IS NULL``).  The best promotion is selected using:
        highest ``discount_percent``, product-scoped over store-wide at
        equal discount, latest ``end_date`` as final tie-breaker.

        Args:
            session: Active async DB session.
            product_id: The product UUID.

        Returns:
            The best matching promotion or ``None``.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Promotion)
            .where(
                Promotion.is_active.is_(True),
                (Promotion.start_date.is_(None))
                | (Promotion.start_date <= now),
                (Promotion.end_date.is_(None))
                | (Promotion.end_date >= now),
                (Promotion.max_uses.is_(None))
                | (Promotion.current_uses < Promotion.max_uses),
                (Promotion.product_id == product_id)
                | (Promotion.product_id.is_(None)),
            )
            .order_by(
                Promotion.discount_percent.desc(),
                # Product-scoped wins tie over store-wide
                Promotion.product_id.is_(None).asc(),
                Promotion.end_date.desc().nullslast(),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_active_for_products(
        self, session: AsyncSession, product_ids: list[UUID]
    ) -> list[Promotion]:
        """Return active promotions for given product IDs (or store-wide)."""
        now = datetime.now(timezone.utc)
        stmt = select(Promotion).where(
            Promotion.is_active.is_(True),
            (Promotion.start_date.is_(None)) | (Promotion.start_date <= now),
            (Promotion.end_date.is_(None)) | (Promotion.end_date >= now),
            (Promotion.max_uses.is_(None))
            | (Promotion.current_uses < Promotion.max_uses),
            (Promotion.product_id.in_(product_ids))
            | (Promotion.product_id.is_(None)),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_paginated(
        self, session: AsyncSession, page: int = 1, per_page: int = 20
    ) -> tuple[list[Promotion], int]:
        from sqlalchemy.orm import selectinload
        stmt = select(Promotion).options(selectinload(Promotion.translations)).order_by(Promotion.created_at.desc())
        return await self.get_paginated(session, stmt=stmt, page=page, per_page=per_page)

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    async def update_fields(
        self,
        session: AsyncSession,
        promotion_id: UUID,
        values: dict,
    ) -> None:
        """Apply a partial field update to a promotion.

        Args:
            session: Active async DB session.
            promotion_id: The promotion UUID.
            values: Dict of column -> value pairs to update.
        """
        from sqlalchemy import update

        await session.execute(
            update(Promotion)
            .where(Promotion.id == promotion_id)
            .values(**values)
        )
        await session.flush()

    async def increment_usage(
        self,
        session: AsyncSession,
        code: str,
    ) -> bool:
        """Atomically increment a promotion's usage counter if under its cap.

        Uses a conditional ``UPDATE ... RETURNING`` so concurrent checkouts
        cannot overshoot ``max_uses`` (TOCTOU-safe).

        Args:
            session: Active async DB session.
            code: The promotion code.

        Returns:
            ``True`` if the counter was incremented (cap not reached),
            ``False`` if the cap is exhausted.
        """
        from sqlalchemy import update

        result = await session.execute(
            update(Promotion)
            .where(Promotion.code == code)
            .where(
                Promotion.max_uses.is_(None)
                | (Promotion.current_uses < Promotion.max_uses)
            )
            .values(current_uses=Promotion.current_uses + 1)
            .returning(Promotion.id)
        )
        return result.scalar_one_or_none() is not None
