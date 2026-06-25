"""Integration tests for VariantService + VariantRepository — real PostgreSQL.

Tests that product variants can be created, listed, updated, and
soft-deleted through the service layer against a real database.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.variant_repository import VariantRepository
from app.schemas.product_variant import ProductVariantCreate, ProductVariantUpdate
from app.services.variant_service import VariantService


@pytest.fixture
def svc() -> VariantService:
    return VariantService()


@pytest.fixture
def vrepo() -> VariantRepository:
    return VariantRepository()


@pytest_asyncio.fixture
async def product(session: AsyncSession) -> Product:
    p = Product(
        slug=f"var-test-{uuid.uuid4().hex[:8]}",
        price=30.00,
    )
    session.add(p)
    await session.flush()
    return p


@pytest.mark.asyncio
async def test_create_and_list_variants(
    session: AsyncSession, svc: VariantService, product: Product
) -> None:
    """Creating a variant and listing it via list_variants."""
    data = ProductVariantCreate(size="M", color="Black", stock=10)
    variant = await svc.create_variant(session, product.id, data)

    assert variant.id is not None
    assert variant.stock == 10

    variants = await svc.list_variants(session, product.id)
    assert len(variants) == 1
    assert variants[0].id == variant.id


@pytest.mark.asyncio
async def test_create_variant_with_sku(
    session: AsyncSession, svc: VariantService, vrepo: VariantRepository, product: Product
) -> None:
    """Creating a variant with explicit SKU and retrieving by SKU."""
    sku = f"SKU-TEST-{uuid.uuid4().hex[:8]}"
    data = ProductVariantCreate(size="L", color="Blue", stock=5, sku=sku)
    await svc.create_variant(session, product.id, data)

    found = await vrepo.get_by_sku(session, sku)
    assert found is not None
    assert found.sku == sku
    assert found.size.value == "L"  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_create_multiple_variants_and_list(
    session: AsyncSession, svc: VariantService, product: Product
) -> None:
    """Creating multiple variants for a product and verifying all are listed."""
    v1 = await svc.create_variant(
        session, product.id, ProductVariantCreate(size="S", color="Red", stock=3)
    )
    v2 = await svc.create_variant(
        session, product.id, ProductVariantCreate(size="M", color="Green", stock=7)
    )

    variants = await svc.list_variants(session, product.id)
    ids = {v.id for v in variants}
    assert len(variants) == 2
    assert v1.id in ids
    assert v2.id in ids


@pytest.mark.asyncio
async def test_update_variant_stock(
    session: AsyncSession, svc: VariantService, product: Product
) -> None:
    """Updating a variant's stock persists correctly."""
    variant = await svc.create_variant(
        session, product.id, ProductVariantCreate(size="XL", stock=20)
    )
    assert variant.stock == 20

    updated = await svc.update_variant(
        session, variant.id, ProductVariantUpdate(stock=50)
    )
    assert updated is not None
    assert updated.stock == 50

    # Verify via repository
    variants = await svc.list_variants(session, product.id)
    assert variants[0].stock == 50


@pytest.mark.asyncio
async def test_soft_delete_variant_excluded_from_listing(
    session: AsyncSession, svc: VariantService, product: Product
) -> None:
    """Soft-deleting a variant excludes it from list_variants."""
    variant = await svc.create_variant(
        session, product.id, ProductVariantCreate(size="M", stock=10)
    )
    assert len(await svc.list_variants(session, product.id)) == 1

    result = await svc.delete_variant(session, variant.id)
    assert result is True

    # After soft-delete, list should be empty
    assert len(await svc.list_variants(session, product.id)) == 0

    # Deleting already-deleted returns False
    result2 = await svc.delete_variant(session, variant.id)
    assert result2 is False
