"""ProductRepository — encapsulates product data access.

Moves all SQLAlchemy query construction out of ``ProductService`` into a
dedicated data-access layer.  The service retains business logic (slug
generation, SKU generation, promotion resolution, variant orchestration).
"""

from datetime import datetime, timezone

from sqlalchemy import and_, case, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.category import Category, CategoryTranslation
from app.models.product import Product, ProductTranslation
from app.models.product_variant import ProductVariant
from app.models.promotion import Promotion
from app.repositories.base import BaseRepository
from app.schemas.common import ProductFilter
from app.utils.pagination import paginate

# Language → PostgreSQL text-search configuration mapping.
# Mirrors the CASE in ``trg_product_translations_search_vector()``
# so queries and trigger use the same dictionary.
LANG_TO_TSCONFIG: dict[str, str] = {
    "es": "spanish",
    "en": "english",
    "sv": "swedish",
}


class ProductRepository(BaseRepository[Product]):
    """Product-specific data access — filtering, eager loading, pagination.

    Usage::

        repo = ProductRepository()
        products, total = await repo.get_with_filters(session, filters)
        product = await repo.get_by_slug(session, "chaqueta-denim")
    """

    def __init__(self) -> None:
        super().__init__(Product)

    # ------------------------------------------------------------------
    # Eager-load presets
    # ------------------------------------------------------------------

    @staticmethod
    def _detail_options() -> list:
        """Eager-load options for single-product detail queries (joinedload)."""
        return [
            joinedload(Product.translations),
            joinedload(Product.category).joinedload(Category.translations),
            joinedload(Product.variants),
        ]

    @staticmethod
    def _list_options() -> list:
        """Eager-load options for product listing queries (selectinload)."""
        return [
            selectinload(Product.translations),
            selectinload(Product.category).selectinload(Category.translations),
            selectinload(Product.variants),
        ]

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_by_slug(
        self,
        session: AsyncSession,
        slug: str,
        *,
        include_deleted: bool = False,
    ) -> Product | None:
        """Fetch a single product by slug with all relationships eager-loaded.

        Args:
            session: Active async DB session.
            slug: The URL slug to look up.
            include_deleted: If ``True``, also return soft-deleted products.

        Returns:
            The product or ``None``.
        """
        where = [Product.slug == slug]
        if not include_deleted:
            where.append(Product.deleted_at.is_(None))
        return await self.find_one(session, *where, options=self._detail_options())

    async def get_by_id_with_detail(
        self,
        session: AsyncSession,
        product_id,
    ) -> Product | None:
        """Fetch a product by ID with all relationships eager-loaded.

        Includes soft-deleted products (used internally by admin flows
        that need to load a product already obtained by ID).
        """
        return await self.get_by_id(
            session, product_id, options=self._detail_options()
        )

    async def get_with_filters(
        self,
        session: AsyncSession,
        filters: ProductFilter,
    ) -> tuple[list[Product], int]:
        """Return a paginated list of non-deleted products matching *filters*.

        Builds the full WHERE clause from the filter object, applies eager
        loading for translations / category / variants, and paginates via
        the existing ``paginate`` utility.

        Returns:
            ``(items, total_count)``.
        """
        stmt = self._build_list_query(filters)
        stmt = stmt.options(*self._list_options())
        return await paginate(
            stmt, session, page=filters.page, per_page=filters.per_page,
        )

    async def get_all_admin(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[Product], int]:
        """Return paginated ALL products (including soft-deleted) for admin.

        Returns:
            ``(items, total_count)``.
        """
        stmt = (
            select(Product)
            .order_by(Product.created_at.desc())
            .options(*self._list_options())
        )
        return await self.get_paginated(
            session, stmt=stmt, page=page, per_page=per_page,
        )

    async def get_by_id_for_resolve(
        self,
        session: AsyncSession,
        product_id,
    ) -> Product | None:
        """Fetch a non-deleted product by ID (no eager loading).

        Used by the controller's UUID-to-slug redirect path.
        """
        return await self.find_one(
            session,
            Product.id == product_id,
            Product.deleted_at.is_(None),
        )

    # ------------------------------------------------------------------
    # Query builder (moved from ProductService._build_list_query)
    # ------------------------------------------------------------------

    def _build_list_query(self, filters: ProductFilter) -> select:
        """Build a ``select(Product)`` from filter criteria.

        Encapsulates all WHERE clauses, JOINs for text search, and the
        stock-priority ordering.  This is pure data-access logic —
        it translates a filter DTO into SQL.
        """
        stmt = select(Product).where(Product.deleted_at.is_(None))

        if filters.category is not None:
            stmt = stmt.where(Product.category_id == filters.category)
        if filters.size is not None:
            stmt = stmt.where(
                exists().where(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.size == filters.size,
                    ProductVariant.deleted_at.is_(None),
                )
            )
        if filters.condition is not None:
            stmt = stmt.where(Product.condition == filters.condition)
        if filters.condition_rating is not None:
            stmt = stmt.where(Product.condition_rating == filters.condition_rating)
        if filters.brand is not None:
            stmt = stmt.where(Product.brand.ilike(f"%{filters.brand}%"))
        if filters.target_gender is not None:
            stmt = stmt.where(Product.target_gender == filters.target_gender)
        if filters.colors is not None:
            color_list = [c.strip() for c in filters.colors.split(",") if c.strip()]
            if color_list:
                stmt = stmt.where(
                    exists().where(
                        ProductVariant.product_id == Product.id,
                        ProductVariant.color.in_(color_list),
                        ProductVariant.deleted_at.is_(None),
                    )
                )
        if filters.material is not None:
            stmt = stmt.where(Product.material.ilike(f"%{filters.material}%"))
        if filters.trend is not None:
            stmt = stmt.where(Product.trend == filters.trend)
        if filters.pattern is not None:
            stmt = stmt.where(Product.pattern == filters.pattern)
        if filters.season is not None:
            stmt = stmt.where(Product.season == filters.season)
        if filters.usage is not None:
            stmt = stmt.where(Product.usage == filters.usage)
        if filters.min_price is not None:
            stmt = stmt.where(Product.price >= filters.min_price)
        if filters.max_price is not None:
            stmt = stmt.where(Product.price <= filters.max_price)

        # has_promotion filter: EXISTS subquery on active promotions
        if filters.has_promotion is True:
            now = datetime.now(timezone.utc)
            promo_exists = exists().where(
                (Promotion.product_id == Product.id)
                | (Promotion.product_id.is_(None)),
                Promotion.is_active == True,
                or_(
                    Promotion.start_date.is_(None),
                    Promotion.start_date <= now,
                ),
                or_(
                    Promotion.end_date.is_(None),
                    Promotion.end_date >= now,
                ),
                or_(
                    Promotion.max_uses.is_(None),
                    Promotion.current_uses < Promotion.max_uses,
                ),
            )
            stmt = stmt.where(promo_exists)

        # Full-text search via tsvector (stemming + GIN index scan).
        # ts_query is captured so the ordering block can apply ts_rank
        # when no explicit sort overrides it.
        ts_query = None

        if filters.q:
            ts_config = LANG_TO_TSCONFIG.get(filters.lang, "simple")
            ts_query = func.plainto_tsquery(ts_config, filters.q)
            stmt = stmt.join(
                ProductTranslation,
                and_(
                    ProductTranslation.product_id == Product.id,
                    ProductTranslation.language_code == filters.lang,
                ),
                isouter=True,
            ).where(
                ProductTranslation.search_vector.op("@@")(ts_query)
            )

        # Ordering — explicit sort options override relevance default
        if filters.sort == "newest":
            return stmt.order_by(Product.created_at.desc())
        if filters.sort == "price_asc":
            return stmt.order_by(Product.price.asc())
        if filters.sort == "price_desc":
            return stmt.order_by(Product.price.desc())

        # Relevance: when a search term is present and no explicit sort
        # was chosen, rank by ts_rank descending.
        if ts_query is not None:
            return stmt.order_by(
                func.ts_rank(ProductTranslation.search_vector, ts_query).desc()
            )

        # Default: products with stock > 0 first, then created_at DESC
        in_stock = (
            exists()
            .where(
                ProductVariant.product_id == Product.id,
                ProductVariant.stock > 0,
                ProductVariant.deleted_at.is_(None),
            )
            .correlate(Product)
        )
        return stmt.order_by(
            case((in_stock, 0), else_=1), Product.created_at.desc()
        )
