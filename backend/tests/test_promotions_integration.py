"""Integration tests for PromotionService + PromotionRepository — real PostgreSQL.

Tests that promotions can be created, listed, and deleted through the
service and repository layers against a real database.  The ``session``
fixture (from ``conftest.py``) provides a fresh transaction per test
that is rolled back automatically.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promotion import Promotion
from app.models.product import Product
from app.repositories.promotion_repository import PromotionRepository
from app.services.promotion_service import PromotionService


@pytest.fixture
def svc() -> PromotionService:
    return PromotionService()


@pytest.fixture
def repo() -> PromotionRepository:
    return PromotionRepository()


async def _create_promo(
    session: AsyncSession,
    *,
    code: str,
    discount_percent: int = 15,
    product_id: uuid.UUID | None = None,
    max_uses: int | None = None,
    current_uses: int = 0,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> Promotion:
    promo = Promotion(
        code=code,
        discount_percent=discount_percent,
        product_id=product_id,
        max_uses=max_uses,
        current_uses=current_uses,
        is_active=True,
        start_date=start_date,
        end_date=end_date,
    )
    session.add(promo)
    await session.flush()
    return promo


@pytest.mark.asyncio
async def test_list_active_returns_created_promotion(
    session: AsyncSession, svc: PromotionService
) -> None:
    """A created active promotion appears in list_active."""
    promo = await _create_promo(session, code=f"ACTIVE-{uuid.uuid4().hex[:8]}")

    active = await svc.list_active(session)
    codes = [p.code for p in active]
    assert promo.code in codes


@pytest.mark.asyncio
async def test_best_for_product_returns_scoped_promo(
    session: AsyncSession, repo: PromotionRepository
) -> None:
    """A product-scoped promotion is returned as best_for_product for its product."""
    product = Product(
        slug=f"best-promo-{uuid.uuid4().hex[:8]}",
        price=50.00,
    )
    session.add(product)
    await session.flush()

    await _create_promo(
        session,
        code=f"PROD-PROMO-{uuid.uuid4().hex[:8]}",
        discount_percent=25,
        product_id=product.id,
    )

    best = await repo.get_best_for_product(session, product.id)
    assert best is not None
    assert best.discount_percent == 25
    assert best.product_id == product.id


@pytest.mark.asyncio
async def test_delete_promotion(
    session: AsyncSession, svc: PromotionService
) -> None:
    """Deleting a promotion removes it via the service."""
    promo = await _create_promo(session, code=f"DEL-{uuid.uuid4().hex[:8]}")

    await svc.delete(session, promo.id)
    await session.flush()

    with pytest.raises(ValueError, match="not found"):
        await svc.get_by_id(session, promo.id)


@pytest.mark.asyncio
async def test_expired_promotion_excluded_from_active(
    session: AsyncSession, svc: PromotionService
) -> None:
    """An expired promotion (end_date in the past) is NOT in list_active."""
    promo = await _create_promo(
        session,
        code=f"EXPIRED-{uuid.uuid4().hex[:8]}",
        discount_percent=20,
        start_date=datetime.now(timezone.utc) - timedelta(days=30),
        end_date=datetime.now(timezone.utc) - timedelta(days=1),
    )

    active = await svc.list_active(session)
    codes = [p.code for p in active]
    assert promo.code not in codes


@pytest.mark.asyncio
async def test_exhausted_promotion_excluded_from_active(
    session: AsyncSession, svc: PromotionService
) -> None:
    """An exhausted promotion (current_uses >= max_uses) is NOT in list_active."""
    promo = await _create_promo(
        session,
        code=f"EXHAUSTED-{uuid.uuid4().hex[:8]}",
        discount_percent=30,
        max_uses=5,
        current_uses=5,
    )

    active = await svc.list_active(session)
    codes = [p.code for p in active]
    assert promo.code not in codes
