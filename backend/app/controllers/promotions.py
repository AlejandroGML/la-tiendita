"""Promotion endpoints — public listing + admin CRUD.

- ``PromotionController`` (``/api/promotions``): public, lists active promos.
- ``AdminPromotionController`` (``/api/admin/promotions``): admin CRUD,
  guarded by ``admin_guard`` (JWT + admin role required).
"""

import math
from uuid import UUID

from litestar import Controller, delete, get, post, put
from litestar.di import Provide
from litestar.exceptions import NotFoundException, ValidationException

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.guards.admin_guard import admin_guard
from app.schemas.promotion import (
    CreatePromotionRequest,
    PromotionResponse,
    UpdatePromotionRequest,
)
from app.services.promotion_service import PromotionService


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_promotion_service() -> PromotionService:
    return PromotionService()


async def provide_session() -> AsyncSession:
    async with _async_session_fn() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Public controller
# ---------------------------------------------------------------------------


class PromotionController(Controller):
    """Public promotion listing — no authentication required.

    Mounted at ``/api/promotions``.
    """

    path = "/api/promotions"
    tags = ["promotions"]
    dependencies = {
        "service": Provide(provide_promotion_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/")
    async def list_active(
        self,
        service: PromotionService,
        session: AsyncSession,
    ) -> list[PromotionResponse]:
        """Return only currently active promotions filtered by date range
        and usage limits.  Public — no authentication required."""
        return await service.list_active(session)


# ---------------------------------------------------------------------------
# Admin controller
# ---------------------------------------------------------------------------


class AdminPromotionController(Controller):
    """Admin promotion CRUD — requires JWT + admin role.

    Mounted at ``/api/admin/promotions``.
    """

    path = "/api/admin/promotions"
    tags = ["admin — promotions"]
    guards = [admin_guard]
    dependencies = {
        "service": Provide(provide_promotion_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/")
    async def list_all(
        self,
        service: PromotionService,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Paginated list of all promotions (admin-only)."""
        items, total = await service.get_all(session, page, per_page)
        return {
            "data": [item.model_dump() for item in items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": max(1, math.ceil(total / per_page)),
            },
        }

    @get("/{promotion_id:uuid}")
    async def get_one(
        self,
        promotion_id: UUID,
        service: PromotionService,
        session: AsyncSession,
    ) -> PromotionResponse:
        """Fetch a single promotion by ID (admin-only)."""
        try:
            return await service.get_by_id(session, promotion_id)
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

    @post("/", status_code=201)
    async def create(
        self,
        data: CreatePromotionRequest,
        service: PromotionService,
        session: AsyncSession,
    ) -> PromotionResponse:
        """Create a new promotion with translations (admin-only)."""
        try:
            return await service.create(session, data)
        except ValueError as exc:
            raise ValidationException(detail=str(exc)) from exc

    @put("/{promotion_id:uuid}")
    async def update(
        self,
        promotion_id: UUID,
        data: UpdatePromotionRequest,
        service: PromotionService,
        session: AsyncSession,
    ) -> PromotionResponse:
        """Update an existing promotion (admin-only). Only provided fields
        are changed.  When translations are provided they replace the old set."""
        try:
            return await service.update(session, promotion_id, data)
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

    @delete("/{promotion_id:uuid}", status_code=204)
    async def delete(
        self,
        promotion_id: UUID,
        service: PromotionService,
        session: AsyncSession,
    ) -> None:
        """Delete a promotion and its translations (admin-only)."""
        try:
            await service.delete(session, promotion_id)
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc
