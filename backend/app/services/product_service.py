"""ProductService — business logic for product catalog CRUD.

Async methods accept SQLAlchemy AsyncSession injection at call time.
"""

import logging
import math
import re
import unicodedata
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.category import Category, CategoryTranslation
from app.models.product import (
    Product,
    ProductCondition,
    ProductSize,
    ProductTranslation,
)
from app.schemas.common import ProductFilter
from app.schemas.product import (
    CreateProductRequest,
    ProductResponse,
    TranslationRequest,
    UpdateProductRequest,
)
from app.utils.pagination import paginate

logger = logging.getLogger(__name__)


class ProductService:
    """Encapsulates all product catalog business logic."""

    # ------------------------------------------------------------------
    # Public read
    # ------------------------------------------------------------------

    async def list_products(
        self,
        session: AsyncSession,
        filters: ProductFilter,
    ) -> tuple[list[Product], int]:
        """Return a paginated list of non-deleted products matching *filters*.

        Translations are eager-loaded via ``selectinload`` to avoid N+1
        on the translations relationship and the category relationship.
        """
        page = filters.page
        per_page = filters.per_page
        lang = filters.lang

        stmt = self._build_list_query(filters)

        # Eager-load translations + category to avoid N+1 in serialisation
        stmt = stmt.options(
            selectinload(Product.translations),
            selectinload(Product.category).selectinload(Category.translations),
        )

        items, total = await paginate(stmt, session, page=page, per_page=per_page)
        return items, total

    async def get_product_by_slug(
        self, session: AsyncSession, slug: str
    ) -> Product | None:
        """Return a single non-deleted product by slug with all translations.

        Uses ``joinedload`` for the single-row detail query.
        """
        stmt = (
            select(Product)
            .where(Product.slug == slug, Product.deleted_at.is_(None))
            .options(
                joinedload(Product.translations),
                joinedload(Product.category).joinedload(Category.translations),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    # ------------------------------------------------------------------
    # Admin write
    # ------------------------------------------------------------------

    async def create_product(
        self, session: AsyncSession, data: CreateProductRequest
    ) -> Product:
        """Create a product with auto-generated slug and translations.

        The Spanish translation name is used for slug generation.
        Falls back to the first translation if no ES is present.
        """
        # Determine the source name for slug generation (prefer ES)
        es = next((t for t in data.translations if t.lang == "es"), None)
        name_for_slug = es.name if es else data.translations[0].name
        slug = await self.generate_slug(session, name_for_slug)

        product = Product(
            slug=slug,
            price=data.price,
            category_id=data.category_id,
            size=ProductSize(data.size) if data.size else None,
            brand=data.brand,
            condition=(
                ProductCondition(data.condition) if data.condition else None
            ),
        )
        session.add(product)
        await session.flush()

        # Persist translations
        for t in data.translations:
            pt = ProductTranslation(
                product_id=product.id,
                language_code=t.lang,
                name=t.name,
                description=t.description,
            )
            session.add(pt)

        await session.flush()

        # Reload with relationships for the response
        return await self._reload_product(session, product.id)

    async def update_product(
        self, session: AsyncSession, product_id: UUID, data: UpdateProductRequest
    ) -> Product | None:
        """Partially update a product and optionally upsert translations.

        Returns the updated product or None if not found / soft-deleted.
        """
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.deleted_at.is_(None))
            .options(
                selectinload(Product.translations),
                selectinload(Product.category).selectinload(Category.translations),
            )
        )
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()
        if product is None:
            return None

        # Scalar fields
        if data.price is not None:
            product.price = data.price
        if data.category_id is not None:
            product.category_id = data.category_id
        if data.size is not None:
            product.size = ProductSize(data.size)
        if data.brand is not None:
            product.brand = data.brand
        if data.condition is not None:
            product.condition = ProductCondition(data.condition)
        if data.image_urls is not None:
            product.image_urls = data.image_urls
        if data.stock is not None:
            product.stock = data.stock

        # Translations upsert
        if data.translations is not None:
            existing_map = {t.language_code: t for t in product.translations}
            for t in data.translations:
                if t.lang in existing_map:
                    existing_map[t.lang].name = t.name
                    existing_map[t.lang].description = t.description
                else:
                    pt = ProductTranslation(
                        product_id=product.id,
                        language_code=t.lang,
                        name=t.name,
                        description=t.description,
                    )
                    session.add(pt)

        await session.flush()
        return product

    async def delete_product(
        self, session: AsyncSession, product_id: UUID
    ) -> bool:
        """Soft-delete a product by setting ``deleted_at`` to now.

        Returns ``True`` if a product was deleted, ``False`` if already
        deleted or not found.
        """
        stmt = select(Product).where(
            Product.id == product_id, Product.deleted_at.is_(None)
        )
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()
        if product is None:
            return False

        product.deleted_at = datetime.now(timezone.utc)
        await session.flush()
        return True

    # ------------------------------------------------------------------
    # Slug generation
    # ------------------------------------------------------------------

    @staticmethod
    def slugify(name: str) -> str:
        """Convert a human-readable name into a URL-safe slug.

        Uses NFKD normalisation to strip accents from Spanish characters
        (e.g. "cañón" → "canon"), then lowercases and replaces runs of
        non-alphanumeric characters with a single hyphen.
        """
        nfkd = unicodedata.normalize("NFKD", name)
        ascii_text = nfkd.encode("ascii", "ignore").decode()
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
        return slug or "producto"

    async def generate_slug(
        self, session: AsyncSession, name: str
    ) -> str:
        """Generate a unique slug from *name*, resolving collisions by
        appending a numeric suffix (``-2``, ``-3``, …).

        Example: "Chaqueta Denim" → "chaqueta-denim". If that slug is
        taken, tries "chaqueta-denim-2", and so on.
        """
        base = self.slugify(name)
        slug = base
        attempt = 1

        while True:
            existing = await session.execute(
                select(Product.id).where(Product.slug == slug)
            )
            if existing.scalar_one_or_none() is None:
                return slug
            attempt += 1
            slug = f"{base}-{attempt}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _reload_product(
        self, session: AsyncSession, product_id: UUID
    ) -> Product:
        """Re-fetch a product with eager-loaded relationships."""
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.translations),
                selectinload(Product.category).selectinload(Category.translations),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    def _build_list_query(self, filters: ProductFilter) -> "select":
        """Build a base select statement from filter criteria."""
        stmt = select(Product).where(Product.deleted_at.is_(None))

        if filters.category is not None:
            stmt = stmt.where(Product.category_id == filters.category)
        if filters.size is not None:
            stmt = stmt.where(Product.size == filters.size)
        if filters.condition is not None:
            stmt = stmt.where(Product.condition == filters.condition)
        if filters.min_price is not None:
            stmt = stmt.where(Product.price >= filters.min_price)
        if filters.max_price is not None:
            stmt = stmt.where(Product.price <= filters.max_price)

        # Full-text search on translations (name OR description)
        if filters.q:
            search_term = f"%{filters.q}%"
            stmt = stmt.join(
                ProductTranslation,
                and_(
                    ProductTranslation.product_id == Product.id,
                    ProductTranslation.language_code == filters.lang,
                ),
                isouter=True,
            ).where(
                or_(
                    ProductTranslation.name.ilike(search_term),
                    ProductTranslation.description.ilike(search_term),
                )
            )

        return stmt.order_by(Product.created_at.desc())
