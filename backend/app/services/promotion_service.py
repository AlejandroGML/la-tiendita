"""PromotionService — admin CRUD + public active listing for discount codes.

Stateless — session injected per-call.  Date-range validation is enforced
at the service layer.  Translations are managed atomically with the parent
promotion (cascade all, delete-orphan).
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.cache import CacheService, cache_service
from app.core.event_bus import event_bus
from app.core.events import AuditAction, AuditEvent, PromotionChangedEvent
from app.models.promotion import Promotion, PromotionTranslation
from app.repositories.promotion_repository import PromotionRepository
from app.schemas.promotion import (
    CreatePromotionRequest,
    PromotionResponse,
    PromotionTranslationResponse,
    UpdatePromotionRequest,
)

logger = logging.getLogger(__name__)


class PromotionService:
    """Encapsulates promotion business logic (admin + public)."""

    def __init__(
        self,
        promotion_repo: PromotionRepository | None = None,
        cache: CacheService | None = None,
    ) -> None:
        self._promotion_repo = promotion_repo or PromotionRepository()
        self._cache = cache or cache_service

    # ------------------------------------------------------------------
    # Public — active promotions
    # ------------------------------------------------------------------

    async def list_active(
        self, session: AsyncSession
    ) -> list[PromotionResponse]:
        """Return promotions that are currently active.

        Results are served through cache-aside keyed by
        ``{prefix}:promotions:active:list`` (TTL ``CACHE_TTL_PROMOTIONS_ACTIVE``).
        When ``CACHE_ENABLED`` is False the cache is bypassed entirely.

        A promotion is active when ALL of these hold:
        - ``is_active = True``
        - ``start_date IS NULL OR start_date <= now()``
        - ``end_date IS NULL OR end_date >= now()``
        - ``max_uses IS NULL OR current_uses < max_uses``

        Results include translations loaded eagerly.
        """
        key: str | None = None
        if settings.CACHE_ENABLED:
            key = f"{settings.CACHE_PREFIX}:promotions:active:list"
            cached = await self._cache.get(key)
            if cached is not None:
                return [PromotionResponse(**item) for item in cached]

        promotions = await self._promotion_repo.get_active(session)
        result = [self._to_response(p) for p in promotions]

        if key is not None:
            await self._cache.set(
                key,
                [r.model_dump(mode="json") for r in result],
                settings.CACHE_TTL_PROMOTIONS_ACTIVE,
            )

        return result

    async def get_active_promotions_for_products(
        self, session: AsyncSession, product_ids: list[UUID]
    ) -> dict[UUID, Promotion]:
        """Return the best active promotion per product_id.

        Queries all active promotions that match any of *product_ids*
        (product-scoped) or are store-wide (``product_id IS NULL``).
        Resolves the best promotion per product in Python using:
        highest ``discount_percent``, product-scoped over store-wide at
        equal discount, latest ``end_date`` as final tie-breaker.

        Returns a dict mapping ``product_id → Promotion``. Products
        with no matching active promotion are absent from the dict.
        """
        if not product_ids:
            return {}

        now = datetime.now(timezone.utc)
        candidates = await self._promotion_repo.get_active_for_products(session, product_ids)

        if not candidates:
            return {}

        # Group by target product_id (store-wide promotions apply to all requested ids)
        by_product: dict[UUID, list[Promotion]] = {pid: [] for pid in product_ids}
        for promo in candidates:
            if promo.product_id is not None and promo.product_id in by_product:
                by_product[promo.product_id].append(promo)
            elif promo.product_id is None:
                # Store-wide — applies to every requested product
                for pid in product_ids:
                    by_product[pid].append(promo)

        # Resolve best per product
        result_map: dict[UUID, Promotion] = {}
        for pid, promos in by_product.items():
            if not promos:
                continue
            best = max(
                promos,
                key=lambda p: (
                    p.discount_percent,
                    1 if p.product_id is not None else 0,  # product-scoped wins tie
                    p.end_date or datetime.max.replace(tzinfo=timezone.utc),
                ),
            )
            result_map[pid] = best

        return result_map

    # ------------------------------------------------------------------
    # Admin CRUD
    # ------------------------------------------------------------------

    async def get_all(
        self, session: AsyncSession, page: int = 1, per_page: int = 20
    ) -> tuple[list[PromotionResponse], int]:
        """Paginated list of all promotions (including inactive/expired).

        Returns ``(items, total)`` so the controller can build pagination.
        """
        promotions, total = await self._promotion_repo.get_all_paginated(
            session, page=page, per_page=per_page
        )

        return [self._to_response(p) for p in promotions], total

    async def get_by_id(
        self, session: AsyncSession, promotion_id: UUID
    ) -> PromotionResponse:
        """Fetch a single promotion by ID with translations.

        Raises ``ValueError`` if not found.
        """
        promotion = await self._promotion_repo.get_by_id(
            session, promotion_id, options=[selectinload(Promotion.translations)]
        )
        if promotion is None:
            raise ValueError(f"Promotion {promotion_id} not found")
        return self._to_response(promotion)

    async def create(
        self,
        session: AsyncSession,
        data: CreatePromotionRequest,
        actor_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> PromotionResponse:
        """Create a promotion with translations.

        Validates that ``start_date < end_date`` when both are provided.
        When *actor_id* is provided, an ``AuditEvent`` is emitted.
        """
        self._validate_dates(data.start_date, data.end_date)

        promotion = Promotion(
            code=data.code,
            discount_percent=data.discount_percent,
            product_id=data.product_id,
            max_uses=data.max_uses,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=data.is_active,
        )
        session.add(promotion)

        # Create translations
        for t_data in data.translations:
            tr = PromotionTranslation(
                promotion=promotion,
                language_code=t_data.language_code,  # type: ignore[arg-type]
                title=t_data.title,
                description=t_data.description,
            )
            session.add(tr)

        await session.flush()
        await session.refresh(promotion, ["translations"])

        # Invalidate affected caches (best-effort, fire-and-forget).
        event_bus.emit(
            PromotionChangedEvent(promotion_id=promotion.id, action="created")
        )
        if actor_id is not None:
            event_bus.emit(
                AuditEvent(
                    actor_id=actor_id,
                    action=AuditAction.PROMOTION_CREATE,
                    entity_type="promotion",
                    entity_id=str(promotion.id),
                    details={"code": promotion.code},
                    ip_address=ip_address,
                )
            )
        return self._to_response(promotion)

    async def update(
        self,
        session: AsyncSession,
        promotion_id: UUID,
        data: UpdatePromotionRequest,
        actor_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> PromotionResponse:
        """Update a promotion.  Only fields present in *data* are changed.

        When ``translations`` are provided the old translations are deleted
        first (cascade) and the new set is inserted.
        When *actor_id* is provided, an ``AuditEvent`` is emitted.
        """
        promotion = await self._get_or_raise(session, promotion_id)

        # Build the SET values dict from non-None fields
        values: dict = {}
        if data.code is not None:
            values["code"] = data.code
        if data.discount_percent is not None:
            values["discount_percent"] = data.discount_percent
        if data.product_id is not None:
            values["product_id"] = data.product_id
        if data.max_uses is not None:
            values["max_uses"] = data.max_uses
        if data.is_active is not None:
            values["is_active"] = data.is_active

        # Date validation — check combined state
        new_start = data.start_date if data.start_date is not None else promotion.start_date
        new_end = data.end_date if data.end_date is not None else promotion.end_date
        self._validate_dates(new_start, new_end)
        if data.start_date is not None:
            values["start_date"] = data.start_date
        if data.end_date is not None:
            values["end_date"] = data.end_date

        if values:
            await self._promotion_repo.update_fields(session, promotion_id, values)

        # Replace translations if provided
        if data.translations is not None:
            # Delete old translations
            await session.execute(
                delete(PromotionTranslation).where(
                    PromotionTranslation.promotion_id == promotion_id
                )
            )
            for t_data in data.translations:
                tr = PromotionTranslation(
                    promotion_id=promotion_id,
                    language_code=t_data.language_code,  # type: ignore[arg-type]
                    title=t_data.title,
                    description=t_data.description,
                )
                session.add(tr)

        await session.flush()
        # Reload from DB to get fresh translations
        response = await self.get_by_id(session, promotion_id)
        # Invalidate affected caches (best-effort, fire-and-forget).
        event_bus.emit(
            PromotionChangedEvent(promotion_id=promotion_id, action="updated")
        )
        if actor_id is not None:
            event_bus.emit(
                AuditEvent(
                    actor_id=actor_id,
                    action=AuditAction.PROMOTION_UPDATE,
                    entity_type="promotion",
                    entity_id=str(promotion_id),
                    details={"code": response.code},
                    ip_address=ip_address,
                )
            )
        return response

    async def delete(
        self,
        session: AsyncSession,
        promotion_id: UUID,
        actor_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete a promotion (cascades to translations).

        Raises ``ValueError`` if the promotion does not exist.
        When *actor_id* is provided, an ``AuditEvent`` is emitted.
        """
        promotion = await self._get_or_raise(session, promotion_id)
        code = promotion.code
        await session.execute(
            delete(Promotion).where(Promotion.id == promotion_id)
        )
        await session.flush()
        # Invalidate affected caches (best-effort, fire-and-forget).
        event_bus.emit(
            PromotionChangedEvent(promotion_id=promotion_id, action="deleted")
        )
        if actor_id is not None:
            event_bus.emit(
                AuditEvent(
                    actor_id=actor_id,
                    action=AuditAction.PROMOTION_DELETE,
                    entity_type="promotion",
                    entity_id=str(promotion_id),
                    details={"code": code},
                    ip_address=ip_address,
                )
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_or_raise(
        self, session: AsyncSession, promotion_id: UUID
    ) -> Promotion:
        """Fetch a promotion by ID or raise ``ValueError``."""
        promotion = await self._promotion_repo.get_by_id(session, promotion_id)
        if promotion is None:
            raise ValueError(f"Promotion {promotion_id} not found")
        return promotion

    @staticmethod
    def _validate_dates(
        start_date: datetime | None, end_date: datetime | None
    ) -> None:
        """Ensure ``start_date < end_date`` when both are set."""
        if start_date is not None and end_date is not None:
            if start_date >= end_date:
                raise ValueError("start_date must be before end_date")

    @staticmethod
    def _to_response(promotion: Promotion) -> PromotionResponse:
        """Convert a Promotion ORM instance to a response DTO."""
        return PromotionResponse(
            id=promotion.id,
            code=promotion.code,
            discount_percent=promotion.discount_percent,
            product_id=promotion.product_id,
            max_uses=promotion.max_uses,
            current_uses=promotion.current_uses,
            is_active=promotion.is_active,
            start_date=promotion.start_date,
            end_date=promotion.end_date,
            translations=[
                PromotionTranslationResponse(
                    lang=t.language_code,  # type: ignore[arg-type]
                    title=t.title,
                    description=t.description,
                )
                for t in promotion.translations
            ],
            created_at=promotion.created_at,
            updated_at=promotion.updated_at,
        )
