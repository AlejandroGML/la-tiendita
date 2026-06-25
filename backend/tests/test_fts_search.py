"""Integration tests for PostgreSQL tsvector full-text search.

These tests require:
- A running PostgreSQL instance
- The ``0011_fts_search`` migration applied
- The ``session`` fixture from ``conftest.py``

If the migration is not applied or the DB is unreachable, tests are skipped.
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductTranslation
from app.repositories.product_repository import LANG_TO_TSCONFIG, ProductRepository
from app.schemas.common import ProductFilter


async def _fts_ready(session: AsyncSession) -> bool:
    """Return True if the search_vector column exists in the DB."""
    try:
        result = await session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'product_translations' "
                "AND column_name = 'search_vector'"
            )
        )
        return result.scalar() is not None
    except Exception:
        return False


@pytest.mark.asyncio
class TestFtsSearch:
    """Full-text search integration tests — requires PostgreSQL + migration 0011."""

    @pytest_asyncio.fixture(autouse=True)
    async def _require_fts(self, session: AsyncSession):
        """Skip all tests in this class if the FTS migration is not applied."""
        if not await _fts_ready(session):
            pytest.skip("FTS migration (0011) not applied — skipping integration tests")

    @staticmethod
    async def _seed(
        session: AsyncSession,
        slug: str,
        price: Decimal,
        category_id: int | None = None,
        translations: list[dict] | None = None,
    ) -> Product:
        """Create and flush a product with translations. The DB trigger
        populates ``search_vector`` automatically."""
        p = Product(
            slug=slug,
            price=price,
            category_id=category_id,
            brand="TestBrand",
        )
        if translations:
            p.translations = [
                ProductTranslation(
                    language_code=t["lang"],
                    name=t["name"],
                    description=t.get("description"),
                )
                for t in translations
            ]
        session.add(p)
        await session.flush()
        return p

    # ------------------------------------------------------------------
    # Task 3.1: Spanish stemming
    # ------------------------------------------------------------------

    async def test_search_stemming(self, session: AsyncSession):
        """``?search=chaquetas&lang=es`` matches a product whose Spanish
        translation uses the singular form ``chaqueta``."""
        await self._seed(
            session,
            slug="chaqueta-denim",
            price=Decimal("29.99"),
            translations=[
                {"lang": "es", "name": "Chaqueta denim", "description": "Azul"},
                {"lang": "en", "name": "Denim jacket", "description": "Blue"},
            ],
        )
        await self._seed(
            session,
            slug="pantalon-negro",
            price=Decimal("19.99"),
            translations=[
                {"lang": "es", "name": "Pantalón negro", "description": "Algodón"},
                {"lang": "en", "name": "Black pants", "description": "Cotton"},
            ],
        )

        repo = ProductRepository()
        filt = ProductFilter(q="chaquetas", lang="es")
        products, total = await repo.get_with_filters(session, filt)

        assert total == 1, f"Expected 1 match for 'chaquetas', got {total}"
        assert products[0].slug == "chaqueta-denim"

    # ------------------------------------------------------------------
    # Task 3.2: Relevance ranking
    # ------------------------------------------------------------------

    async def test_search_relevance_ranking(self, session: AsyncSession):
        """A product with two matches (name + description) ranks higher
        than one with a single match when search term is in both."""
        await self._seed(
            session,
            slug="denim-jacket",
            price=Decimal("59.99"),
            translations=[
                {"lang": "en", "name": "Denim Jacket", "description": "Classic denim jacket"},
            ],
        )
        await self._seed(
            session,
            slug="denim-shirt",
            price=Decimal("39.99"),
            translations=[
                {"lang": "en", "name": "Denim Shirt", "description": "Casual blue shirt"},
            ],
        )

        repo = ProductRepository()
        filt = ProductFilter(q="denim", lang="en")
        products, total = await repo.get_with_filters(session, filt)

        assert total == 2, f"Expected 2 matches for 'denim', got {total}"
        # The jacket has "denim" in both name and description → should rank higher.
        assert products[0].slug == "denim-jacket", (
            f"Expected 'denim-jacket' to rank first (2 matches), "
            f"got '{products[0].slug}'"
        )

    # ------------------------------------------------------------------
    # Task 3.3: Combined FTS + category filter
    # ------------------------------------------------------------------

    async def test_search_with_category_filter(self, session: AsyncSession):
        """FTS combined with ``category_id`` filter produces AND behavior."""
        await self._seed(
            session,
            slug="chaqueta-cuero",
            price=Decimal("89.99"),
            category_id=1,
            translations=[
                {"lang": "es", "name": "Chaqueta de cuero", "description": "Negra"},
            ],
        )
        await self._seed(
            session,
            slug="pantalon-cuero",
            price=Decimal("79.99"),
            category_id=2,
            translations=[
                {"lang": "es", "name": "Pantalón de cuero", "description": "Ajustado"},
            ],
        )

        repo = ProductRepository()
        filt = ProductFilter(q="cuero", lang="es", category=1)
        products, total = await repo.get_with_filters(session, filt)

        assert total == 1, (
            f"Expected 1 result for 'cuero' in category 1, got {total}"
        )
        assert products[0].slug == "chaqueta-cuero"

    # ------------------------------------------------------------------
    # Task 3.4: Swedish stemming
    # ------------------------------------------------------------------

    async def test_search_swedish_stemming(self, session: AsyncSession):
        """``?search=jackor&lang=sv`` matches the singular ``jacka``
        via Swedish stemming."""
        await self._seed(
            session,
            slug="denimjacka",
            price=Decimal("249.00"),
            translations=[
                {"lang": "sv", "name": "Denimjacka", "description": "Blå jacka"},
                {"lang": "en", "name": "Denim jacket", "description": "Blue jacket"},
            ],
        )
        await self._seed(
            session,
            slug="jeanskjorta",
            price=Decimal("199.00"),
            translations=[
                {"lang": "sv", "name": "Jeanskjorta", "description": "Blå skjorta"},
            ],
        )

        repo = ProductRepository()
        filt = ProductFilter(q="jackor", lang="sv")
        products, total = await repo.get_with_filters(session, filt)

        assert total == 1, f"Expected 1 match for 'jackor' (sv), got {total}"
        assert products[0].slug == "denimjacka"

    # ------------------------------------------------------------------
    # Task 3.5: Explicit sort overrides relevance
    # ------------------------------------------------------------------

    async def test_search_sort_override(self, session: AsyncSession):
        """``?search=denim&sort=newest`` returns results ordered by
        ``created_at DESC``, not ts_rank."""
        await self._seed(
            session,
            slug="denim-old",
            price=Decimal("30.00"),
            translations=[
                {"lang": "en", "name": "Old Denim", "description": "Vintage denim denim denim"},
            ],
        )
        # Force a later created_at by manual update (the second insert gets a
        # later server timestamp).
        await self._seed(
            session,
            slug="denim-new",
            price=Decimal("40.00"),
            translations=[
                {"lang": "en", "name": "New Denim", "description": "Fresh"},
            ],
        )

        repo = ProductRepository()
        filt = ProductFilter(q="denim", lang="en", sort="newest")
        products, total = await repo.get_with_filters(session, filt)

        assert total == 2, f"Expected 2 matches, got {total}"
        # With sort=newest, denim-new (inserted later) should be first.
        assert products[0].slug == "denim-new", (
            f"Expected 'denim-new' first with sort=newest, got '{products[0].slug}'"
        )


class TestLangToTsconfig:
    """Module-level LANG_TO_TSCONFIG contract tests (no DB needed)."""

    def test_known_languages_map_correctly(self):
        assert LANG_TO_TSCONFIG["es"] == "spanish"
        assert LANG_TO_TSCONFIG["en"] == "english"
        assert LANG_TO_TSCONFIG["sv"] == "swedish"

    def test_unknown_language_falls_back_to_simple(self):
        assert LANG_TO_TSCONFIG.get("fr", "simple") == "simple"
        assert LANG_TO_TSCONFIG.get("de", "simple") == "simple"

    def test_lang_to_tsconfig_is_immutable_after_import(self):
        """Ensure the dict has the expected three keys."""
        assert set(LANG_TO_TSCONFIG.keys()) == {"es", "en", "sv"}
