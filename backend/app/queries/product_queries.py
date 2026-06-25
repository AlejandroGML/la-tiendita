"""Read-optimized CQRS query layer for product listings.

Uses minimal joins and correlated subqueries instead of eager-loading
entire relationship graphs. Returns lightweight DTOs directly, avoiding
ORM hydration of full variant/translation/category trees.
"""

import math
import re
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.product import Product, ProductTranslation
from app.models.product_variant import ProductVariant
from app.models.promotion import Promotion
from app.schemas.common import ProductFilter
from app.schemas.product import ProductSummaryDTO

# Language → PostgreSQL text-search configuration mapping.
# Mirrors the CASE in ``trg_product_translations_search_vector()``
# so queries and trigger use the same dictionary.
LANG_TO_TSCONFIG: dict[str, str] = {
    "es": "spanish",
    "en": "english",
    "sv": "swedish",
}

SIZE_ORDER: dict[str, int] = {
    "XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5,
}


class ProductQueries:
    """Read-optimized queries for product listings.

    Uses correlated subqueries for stock/promotion instead of eager loading
    variant arrays, and LEFT JOINs only the requested translation language
    instead of loading all translations.

    Usage::

        queries = ProductQueries()
        summaries, total = await queries.get_summaries(session, filters)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_summaries(
        self, session: AsyncSession, filters: ProductFilter
    ) -> tuple[list[ProductSummaryDTO], int]:
        """Return paginated product summaries for listing.

        Builds a lightweight SELECT with:
        - LEFT JOIN on product_translations for the requested lang only
        - Correlated subquery for stock_total (SUM of variant stocks)
        - Correlated subquery for has_promotion (EXISTS on active promos)

        After the main query, a separate aggregation fetches variant-derived
        fields (colors, sizes, has_variants) for the returned product IDs.
        """
        stmt = self._build_summary_query(filters)

        # Count total matching rows
        count_stmt = select(func.count()).select_from(
            stmt.order_by(None).subquery()
        )
        total: int = (await session.execute(count_stmt)).scalar_one()

        total_pages = max(1, math.ceil(total / filters.per_page))
        page = max(1, min(filters.page, total_pages))
        offset = (page - 1) * filters.per_page
        paged_stmt = stmt.limit(filters.per_page).offset(offset)

        result = await session.execute(paged_stmt)
        rows = result.all()

        summaries: list[ProductSummaryDTO] = []
        product_ids: list[UUID] = []

        for row in rows:
            product: Product = row[0]
            name: str | None = row[1]  # summary_name
            stock_total: int = row[2] or 0  # stock_total
            has_promotion: bool = row[3] or False  # has_promotion

            product_ids.append(product.id)

            summaries.append(
                ProductSummaryDTO(
                    id=product.id,
                    slug=product.slug,
                    name=name or _slug_to_display_name(product.slug),
                    price=Decimal(str(product.price)),
                    condition=(
                        product.condition.value if product.condition else None
                    ),
                    condition_rating=product.condition_rating,
                    brand=product.brand,
                    material=product.material,
                    image_urls=(
                        list(product.image_urls)
                        if product.image_urls
                        else []
                    ),
                    stock_total=stock_total,
                    has_promotion=has_promotion,
                    created_at=product.created_at,
                    sale_price=None,
                    discount_label=None,
                    promotion=None,
                    colors=None,
                    sizes=None,
                    has_variants=False,
                    is_out_of_stock=False,
                )
            )

        # Post-query: variant-derived fields (colors, sizes, has_variants)
        if summaries:
            await self._enrich_variant_data(session, summaries, product_ids)

        return summaries, total

    # ------------------------------------------------------------------
    # Query builder
    # ------------------------------------------------------------------

    def _build_summary_query(self, filters: ProductFilter) -> Select:
        """Build a select(Product) with subqueries for stock and promotion.

        Applies the same filter criteria as ProductRepository._build_list_query.
        """
        lang = filters.lang

        # ---- Correlated subqueries ----

        stock_total_subq = (
            select(func.coalesce(func.sum(ProductVariant.stock), 0))
            .where(
                ProductVariant.product_id == Product.id,
                ProductVariant.deleted_at.is_(None),
            )
            .correlate(Product)
            .scalar_subquery()
            .label("stock_total")
        )

        now = datetime.now(timezone.utc)
        has_promo_subq = (
            exists()
            .where(
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
            .correlate(Product)
            .label("has_promotion")
        )

        # Translation name for requested lang (NULL if no translation exists;
        # fallback to slug humanization happens in Python)
        translation_name_subq = (
            select(ProductTranslation.name)
            .where(
                ProductTranslation.product_id == Product.id,
                ProductTranslation.language_code == lang,
            )
            .correlate(Product)
            .scalar_subquery()
            .label("summary_name")
        )

        # ---- Base query ----

        stmt = (
            select(
                Product,
                translation_name_subq,
                stock_total_subq,
                has_promo_subq,
            )
            .where(Product.deleted_at.is_(None))
        )

        # ---- Apply filters (same logic as ProductRepository._build_list_query) ----

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
            color_list = [
                c.strip() for c in filters.colors.split(",") if c.strip()
            ]
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

        # has_promotion filter
        if filters.has_promotion is True:
            stmt = stmt.where(has_promo_subq)

        # Full-text search
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

        # ---- Ordering ----

        if filters.sort == "newest":
            return stmt.order_by(Product.created_at.desc())
        if filters.sort == "price_asc":
            return stmt.order_by(Product.price.asc())
        if filters.sort == "price_desc":
            return stmt.order_by(Product.price.desc())

        if ts_query is not None:
            return stmt.order_by(
                func.ts_rank(ProductTranslation.search_vector, ts_query).desc()
            )

        # Default: in-stock first, then newest
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

    # ------------------------------------------------------------------
    # Variant enrichment (post-query)
    # ------------------------------------------------------------------

    async def _enrich_variant_data(
        self,
        session: AsyncSession,
        summaries: list[ProductSummaryDTO],
        product_ids: list[UUID],
    ) -> None:
        """Fetch variant-derived fields (colors, sizes) for a batch of products.

        Runs a single aggregation query for all product IDs, then updates
        each summary in-place.
        """
        if not product_ids:
            return

        # Aggregate unique color+hex pairs per product
        color_rows = await session.execute(
            select(
                ProductVariant.product_id,
                ProductVariant.color,
                ProductVariant.color_hex,
            )
            .where(
                ProductVariant.product_id.in_(product_ids),
                ProductVariant.deleted_at.is_(None),
                ProductVariant.color.isnot(None),
            )
            .distinct()
        )

        # Aggregate unique sizes per product
        size_rows = await session.execute(
            select(
                ProductVariant.product_id,
                ProductVariant.size,
            )
            .where(
                ProductVariant.product_id.in_(product_ids),
                ProductVariant.deleted_at.is_(None),
                ProductVariant.size.isnot(None),
            )
            .distinct()
        )

        # Count variants per product
        variant_count_rows = await session.execute(
            select(
                ProductVariant.product_id,
                func.count(ProductVariant.id).label("cnt"),
            )
            .where(
                ProductVariant.product_id.in_(product_ids),
                ProductVariant.deleted_at.is_(None),
            )
            .group_by(ProductVariant.product_id)
        )

        # Build lookup maps
        colors_map: dict[UUID, list[dict]] = {}
        for row in color_rows:
            pid: UUID = row[0]
            color: str = row[1]
            hex_val: str | None = row[2]
            if pid not in colors_map:
                colors_map[pid] = []
            colors_map[pid].append({"color": color, "hex": hex_val or ""})

        sizes_map: dict[UUID, list[str]] = {}
        for row in size_rows:
            pid: UUID = row[0]
            # size is stored as ProductSize enum string value in DB
            size_val = row[1]
            size_str = (
                size_val.value if hasattr(size_val, "value") else str(size_val)
            )
            if pid not in sizes_map:
                sizes_map[pid] = []
            if size_str not in sizes_map[pid]:
                sizes_map[pid].append(size_str)

        variant_count_map: dict[UUID, int] = {}
        for row in variant_count_rows:
            variant_count_map[row[0]] = row[1]

        # Sort sizes by SIZE_ORDER
        for pid in sizes_map:
            sizes_map[pid].sort(
                key=lambda s: SIZE_ORDER.get(s, 999)
            )

        # Apply to summaries
        for s in summaries:
            colors = colors_map.get(s.id, [])
            sizes = sizes_map.get(s.id, [])
            vc = variant_count_map.get(s.id, 0)

            s.colors = colors if colors else None
            s.sizes = sizes if sizes else None
            s.has_variants = vc > 1 or (
                vc == 1 and (len(colors) > 0 or len(sizes) > 0)
            )
            s.is_out_of_stock = s.has_variants and s.stock_total == 0


def _slug_to_display_name(slug: str) -> str:
    """Humanize a slug when no translation exists.

    Example: "chaqueta-denim" → "Chaqueta Denim"
    """
    if not slug:
        return ""
    # Strip trailing hash segment if present e.g. "chaqueta-a1b2c3d4"
    parts = slug.split("-")
    if len(parts) > 1 and re.match(r"^[0-9a-f]{8,}$", parts[-1].lower()):
        cleaned = "-".join(parts[:-1])
    else:
        cleaned = slug
    return " ".join(
        w.capitalize() for w in cleaned.replace("-", " ").split()
    )
