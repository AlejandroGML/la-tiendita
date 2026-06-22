"""Integration tests for dataset seeding data integrity.

Tests roundtrip (insert → read), null safety, JSONB serialization,
slug uniqueness, FK integrity, batch consistency, boundary values,
and Swedish character encoding preservation.

These tests use the real PostgreSQL test database directly (no mocks).
"""

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category, CategoryTranslation
from app.models.product import Product, ProductCondition, ProductTranslation
from app.services.product_service import ProductService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def svc() -> ProductService:
    return ProductService()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest_asyncio.fixture
async def category(session: AsyncSession) -> Category:
    """Create a test category for FK integrity tests."""
    unique_slug = f"test-category-{_uid()}"
    cat = Category(slug=unique_slug)
    session.add(cat)
    await session.flush()
    session.add(CategoryTranslation(category_id=cat.id, language_code="en", name="Test Category"))
    session.add(CategoryTranslation(category_id=cat.id, language_code="es", name="Categoría Test"))
    await session.flush()
    return cat


# ---------------------------------------------------------------------------
# Test: Full roundtrip with all dataset fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_roundtrip_all_fields(svc: ProductService, session: AsyncSession, category: Category):
    """Insert a product with every dataset field populated, then read it back and verify."""
    slug = f"roundtrip-{_uid()}"
    product = Product(
        slug=slug,
        price=Decimal("75.00"),
        category_id=category.id,
        brand="H&M",
        condition=ProductCondition.GOOD,
        condition_rating=3,
        condition_details={
            "pilling": 2,
            "damage": "Small tear on sleeve",
            "stains": "Yes",
            "holes": "No",
            "smell": "No",
        },
        target_gender="Ladies",
        material="95%cotton 5%elastan",
        colors=["Pink", "Blue", "White"],
        trend="Sports",
        pattern="Striped",
        season="Summer",
        cut=["V-collar", "Cropped"],
        usage="Reuse",
        source_dataset="fnauman/fashion-second-hand",
        stock=5,
    )
    session.add(product)
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()

    assert p.slug == slug
    assert p.price == Decimal("75.00")
    assert p.category_id == category.id
    assert p.brand == "H&M"
    assert p.condition == ProductCondition.GOOD
    assert p.condition_rating == 3
    assert p.condition_details == {
        "pilling": 2,
        "damage": "Small tear on sleeve",
        "stains": "Yes",
        "holes": "No",
        "smell": "No",
    }
    assert p.target_gender == "Ladies"
    assert p.material == "95%cotton 5%elastan"
    assert p.colors == ["Pink", "Blue", "White"]
    assert p.trend == "Sports"
    assert p.pattern == "Striped"
    assert p.season == "Summer"
    assert p.cut == ["V-collar", "Cropped"]
    assert p.usage == "Reuse"
    assert p.source_dataset == "fnauman/fashion-second-hand"
    assert p.stock == 5
    assert p.deleted_at is None


# ---------------------------------------------------------------------------
# Test: Null safety — all optional fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_null_fields_persist_as_none(svc: ProductService, session: AsyncSession):
    """Optional dataset fields should persist and return as None."""
    slug = f"null-fields-{_uid()}"
    product = Product(slug=slug, price=Decimal("10.00"))
    session.add(product)
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()

    assert p.condition_rating is None
    assert p.condition_details is None
    assert p.target_gender is None
    assert p.material is None
    assert p.colors is None
    assert p.trend is None
    assert p.pattern is None
    assert p.season is None
    assert p.cut is None
    assert p.usage is None
    assert p.source_dataset is None


# ---------------------------------------------------------------------------
# Test: JSONB serialization / deserialization roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jsonb_lists_roundtrip(svc: ProductService, session: AsyncSession):
    """colors and cut (JSONB arrays) should survive a roundtrip intact."""
    slug = f"jsonb-list-{_uid()}"
    product = Product(slug=slug, price=Decimal("20.00"), colors=["Red", "Green", "Blue"], cut=["Collar", "Long sleeve"])
    session.add(product)
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()
    assert p.colors == ["Red", "Green", "Blue"]
    assert p.cut == ["Collar", "Long sleeve"]


@pytest.mark.asyncio
async def test_jsonb_empty_list_persists(svc: ProductService, session: AsyncSession):
    """Empty JSONB list should persist as empty list, not None."""
    slug = f"jsonb-empty-{_uid()}"
    product = Product(slug=slug, price=Decimal("20.00"), colors=[], cut=[])
    session.add(product)
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()
    assert p.colors == []
    assert p.cut == []


# ---------------------------------------------------------------------------
# Test: Slug uniqueness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slugs_are_unique(svc: ProductService, session: AsyncSession):
    """Insert multiple products and verify no slug collisions."""
    prefix = f"uniq-{_uid()}"
    slugs = [f"{prefix}-{i}" for i in range(10)]
    for i, slug in enumerate(slugs):
        session.add(Product(slug=slug, price=Decimal(f"{10 + i}.00")))
    await session.commit()

    result = await session.execute(select(Product.slug).where(Product.slug.in_(slugs)))
    found = set(result.scalars().all())
    assert found == set(slugs)
    assert len(found) == 10


# ---------------------------------------------------------------------------
# Test: FK integrity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fk_category_exists(svc: ProductService, session: AsyncSession, category: Category):
    """Products with a valid category_id should reference an existing category."""
    slug = f"fk-{_uid()}"
    session.add(Product(slug=slug, price=Decimal("30.00"), category_id=category.id))
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()
    assert p.category_id == category.id

    cat_result = await session.execute(select(Category).where(Category.id == category.id))
    assert cat_result.scalar_one() is not None


# ---------------------------------------------------------------------------
# Test: Batch consistency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_insert_no_lost_rows(svc: ProductService, session: AsyncSession):
    """Insert 50 products in a batch and verify all are retrievable."""
    prefix = f"batch-{_uid()}"
    batch = [Product(slug=f"{prefix}-{i}", price=Decimal(f"{5 + i}.00")) for i in range(50)]
    session.add_all(batch)
    await session.commit()

    count = await session.execute(
        select(func.count()).select_from(Product).where(Product.slug.like(f"{prefix}-%"))
    )
    assert count.scalar() == 50

    # Cleanup
    await session.execute(delete(Product).where(Product.slug.like(f"{prefix}-%")))
    await session.commit()


# ---------------------------------------------------------------------------
# Test: Boundary values
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_condition_rating_boundaries(svc: ProductService, session: AsyncSession):
    """condition_rating should accept integers 1-5."""
    prefix = f"boundary-{_uid()}"
    slugs = {}
    for rating in [1, 3, 5]:
        s = f"{prefix}-{rating}"
        session.add(Product(slug=s, price=Decimal("15.00"), condition_rating=rating))
        slugs[rating] = s
    await session.commit()

    for rating, s in slugs.items():
        result = await session.execute(select(Product).where(Product.slug == s))
        p = result.scalar_one()
        assert p.condition_rating == rating

    # Cleanup
    for s in slugs.values():
        await session.execute(delete(Product).where(Product.slug == s))
    await session.commit()


@pytest.mark.asyncio
async def test_price_positive(svc: ProductService, session: AsyncSession):
    """Price must be > 0."""
    slug = f"positive-{_uid()}"
    session.add(Product(slug=slug, price=Decimal("0.01")))
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()
    assert p.price > 0

    # Cleanup
    await session.execute(delete(Product).where(Product.slug == slug))
    await session.commit()


@pytest.mark.asyncio
async def test_material_with_percentages(svc: ProductService, session: AsyncSession):
    """Material strings with % should be preserved."""
    material = "95%cotton 5%elastan"
    slug = f"material-{_uid()}"
    session.add(Product(slug=slug, price=Decimal("20.00"), material=material))
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()
    assert p.material == material

    # Cleanup
    await session.execute(delete(Product).where(Product.slug == slug))
    await session.commit()


# ---------------------------------------------------------------------------
# Test: Swedish character encoding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_swedish_characters_preserved(svc: ProductService, session: AsyncSession):
    """Swedish characters (å, ä, ö) in brand, material, and translations should be preserved."""
    slug = f"swedish-{_uid()}"
    product = Product(slug=slug, price=Decimal("40.00"), brand="KappAhl", material="100% bomull")
    session.add(product)
    await session.flush()

    session.add(ProductTranslation(
        product_id=product.id, language_code="sv",
        name="Skjorta med blommönster",
        description="En fin skjorta från KappAhl. Mycket skön att bära på sommaren.",
    ))
    await session.commit()

    result = await session.execute(
        select(Product).where(Product.slug == slug).options(selectinload(Product.translations))
    )
    p = result.scalar_one()
    assert p.brand == "KappAhl"
    assert p.material == "100% bomull"

    assert len(p.translations) == 1
    t = p.translations[0]
    assert t.language_code == "sv"
    assert "blommönster" in t.name
    assert "skön" in t.description
    assert "KappAhl" in t.description
    assert "sommaren" in t.description

    # Cleanup
    await session.execute(delete(Product).where(Product.slug == slug))
    await session.commit()


# ---------------------------------------------------------------------------
# Test: Multi-translation product
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_product_with_multiple_translations(svc: ProductService, session: AsyncSession):
    """A product should support multiple translations (EN + SV)."""
    slug = f"multi-lang-{_uid()}"
    product = Product(slug=slug, price=Decimal("50.00"))
    session.add(product)
    await session.flush()

    session.add(ProductTranslation(product_id=product.id, language_code="en", name="Blue Denim Jacket", description="A classic denim jacket in blue."))
    session.add(ProductTranslation(product_id=product.id, language_code="sv", name="Blå Denimjacka", description="En klassisk denimjacka i blått."))
    await session.commit()

    result = await session.execute(
        select(Product).where(Product.slug == slug).options(selectinload(Product.translations))
    )
    p = result.scalar_one()
    assert len(p.translations) == 2
    names = {t.language_code: t.name for t in p.translations}
    assert names["en"] == "Blue Denim Jacket"
    assert names["sv"] == "Blå Denimjacka"

    # Cleanup
    await session.execute(delete(Product).where(Product.slug == slug))
    await session.commit()


# ---------------------------------------------------------------------------
# Test: condition_details partial population
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_condition_details_partial(svc: ProductService, session: AsyncSession):
    """condition_details should support partial data (only some keys)."""
    slug = f"partial-cond-{_uid()}"
    session.add(Product(slug=slug, price=Decimal("25.00"), condition_details={"pilling": 2}))
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()
    assert p.condition_details == {"pilling": 2}

    # Cleanup
    await session.execute(delete(Product).where(Product.slug == slug))
    await session.commit()


@pytest.mark.asyncio
async def test_condition_details_empty_dict(svc: ProductService, session: AsyncSession):
    """Empty condition_details dict should persist as empty dict."""
    slug = f"empty-cond-{_uid()}"
    session.add(Product(slug=slug, price=Decimal("25.00"), condition_details={}))
    await session.commit()

    result = await session.execute(select(Product).where(Product.slug == slug))
    p = result.scalar_one()
    assert p.condition_details == {}

    # Cleanup
    await session.execute(delete(Product).where(Product.slug == slug))
    await session.commit()
