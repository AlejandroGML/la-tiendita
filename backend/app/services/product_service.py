"""ProductService — business logic for product catalog CRUD.

Async methods accept SQLAlchemy AsyncSession injection at call time.
Data access is delegated to ``ProductRepository`` — the service only
handles business logic (promotion resolution, translation orchestration,
product CRUD).  Slug generation and variant CRUD are delegated to
``SlugService`` and ``VariantService`` respectively.
"""

import logging
import math
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.cache import CacheService, cache_service
from app.core.event_bus import event_bus
from app.core.events import ProductChangedEvent
from app.models.product import Product, ProductCondition, ProductTranslation
from app.repositories.product_repository import ProductRepository
from app.schemas.common import ProductFilter
from app.schemas.product import (
    CreateProductRequest,
    UpdateProductRequest,
)
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
)
from app.serializers.product import build_product_response
from app.services.slug_service import SlugService
from app.services.variant_service import VariantService

logger = logging.getLogger(__name__)


class ProductService:
    """Encapsulates all product catalog business logic.

    Injects ``ProductRepository``, ``SlugService``, and ``VariantService``.
    If no service is provided, default instances are created (backward-compatible
    for direct instantiation in tests). An optional ``cache`` (a
    :class:`CacheService`) may be injected for fakeredis-backed tests; the
    module singleton is used by default.
    """

    def __init__(
        self,
        product_repo: ProductRepository | None = None,
        slug_service: SlugService | None = None,
        variant_service: VariantService | None = None,
        cache: CacheService | None = None,
    ) -> None:
        self._repo = product_repo or ProductRepository()
        self._slug_service = slug_service or SlugService()
        self._variant_service = variant_service or VariantService(product_repo=self._repo)
        self._cache = cache or cache_service

    # ------------------------------------------------------------------
    # Public read
    # ------------------------------------------------------------------

    async def list_products(
        self,
        session: AsyncSession,
        filters: ProductFilter,
    ) -> tuple[list[Product], int]:
        """Return a paginated list of non-deleted products matching *filters*.

        Delegates filtering + eager loading + pagination to the repository.
        """
        return await self._repo.get_with_filters(session, filters)

    async def list_admin_products(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[Product], int]:
        """Return a paginated list of ALL products (including soft-deleted)
        for the admin panel."""
        return await self._repo.get_all_admin(session, page=page, per_page=per_page)

    async def get_product_by_slug(
        self, session: AsyncSession, slug: str
    ) -> Product | None:
        """Return a single non-deleted product by slug with all relationships."""
        return await self._repo.get_by_slug(session, slug)

    # ------------------------------------------------------------------
    # Public read — cache-aside (return serialized response dicts)
    # ------------------------------------------------------------------

    # Filter dimensions that make a listing non-cacheable. Only the default
    # unfiltered listing (lang + page + per_page) is ever cached; every
    # filtered query bypasses the cache to avoid low hit rates and bloat.
    _FILTER_FIELDS = (
        "category",
        "size",
        "condition",
        "condition_rating",
        "brand",
        "target_gender",
        "material",
        "trend",
        "pattern",
        "season",
        "usage",
        "colors",
        "min_price",
        "max_price",
        "has_promotion",
        "sort",
        "q",
    )

    @classmethod
    def _has_active_filters(cls, filters: ProductFilter) -> bool:
        """Return True when any non-pagination filter is set."""
        return any(getattr(filters, f) is not None for f in cls._FILTER_FIELDS)

    def _list_cache_key(self, filters: ProductFilter) -> str:
        """Build the deterministic list cache key (default listing only)."""
        return (
            f"{settings.CACHE_PREFIX}:products:list:"
            f"{filters.lang}:{filters.page}:{filters.per_page}:default"
        )

    async def list_products_cached(
        self, session: AsyncSession, filters: ProductFilter
    ) -> dict:
        """Return the full public listing response dict via cache-aside.

        Only the default unfiltered listing is cached. Filtered requests fall
        through to the repository on every call (no cache read or write). When
        ``CACHE_ENABLED`` is False the cache is bypassed entirely, producing
        byte-identical behavior to the uncached baseline.
        """
        cacheable = settings.CACHE_ENABLED and not self._has_active_filters(filters)
        key = self._list_cache_key(filters) if cacheable else None

        if key is not None:
            cached = await self._cache.get(key)
            if cached is not None:
                return cached

        items, total = await self._repo.get_with_filters(session, filters)
        promotions = await self._apply_promotions(session, items)
        data = [
            build_product_response(p, lang=filters.lang, promotion_info=promotions)
            for p in items
        ]

        response = {
            "data": data,
            "pagination": {
                "page": filters.page,
                "per_page": filters.per_page,
                "total": total,
                "pages": max(1, math.ceil(total / filters.per_page)),
            },
            "meta": {
                "lang": filters.lang,
                "category_id": filters.category,
                "size": filters.size,
                "condition": filters.condition,
                "condition_rating": filters.condition_rating,
                "brand": filters.brand,
                "target_gender": filters.target_gender,
                "material": filters.material,
                "trend": filters.trend,
                "pattern": filters.pattern,
                "season": filters.season,
                "usage": filters.usage,
                "min_price": str(filters.min_price) if filters.min_price else None,
                "max_price": str(filters.max_price) if filters.max_price else None,
                "has_promotion": filters.has_promotion,
                "sort": filters.sort,
                "search": filters.q,
            },
        }

        if key is not None:
            await self._cache.set(key, response, settings.CACHE_TTL_PRODUCTS_LIST)

        return response

    async def get_product_by_slug_cached(
        self, session: AsyncSession, slug: str
    ) -> dict | None:
        """Return the full product detail response dict via cache-aside.

        Detail keys are lang-independent (the detail endpoint returns all
        translations). Returns ``None`` when the product does not exist. When
        ``CACHE_ENABLED`` is False the cache is bypassed entirely.
        """
        key: str | None = None
        if settings.CACHE_ENABLED:
            key = f"{settings.CACHE_PREFIX}:products:detail:{slug}"
            cached = await self._cache.get(key)
            if cached is not None:
                return cached

        product = await self._repo.get_by_slug(session, slug)
        if product is None:
            return None

        promotions = await self._apply_promotions(session, [product])
        response = build_product_response(product, promotion_info=promotions)

        if key is not None:
            await self._cache.set(key, response, settings.CACHE_TTL_PRODUCTS_DETAIL)

        return response

    async def _apply_promotions(
        self, session: AsyncSession, products: list[Product]
    ) -> dict[UUID, dict]:
        """Resolve active promotions and compute sale pricing for *products*.

        Creates a local ``PromotionService`` instance, resolves the best
        active promotion per product, and computes ``sale_price`` for each
        product that has a matching promotion.  The frontend derives
        discount labels from ``promotion.discount_percent``.

        Returns a dict ``product_id → {promotion, sale_price}``.
        Products without an active promotion are absent from the dict.
        """
        if not products:
            return {}

        from app.services.promotion_service import PromotionService

        promo_service = PromotionService()
        product_ids = [p.id for p in products]
        best_promos = await promo_service.get_active_promotions_for_products(
            session, product_ids
        )

        result: dict[UUID, dict] = {}
        for product in products:
            promo = best_promos.get(product.id)
            if promo is None:
                continue
            from decimal import Decimal as _Decimal

            result[product.id] = {
                "promotion": promo,
                "sale_price": round(
                    product.price * (1 - promo.discount_percent / 100), 2
                ),
            }

        return result

    # ------------------------------------------------------------------
    # Admin write
    # ------------------------------------------------------------------

    async def create_product(
        self, session: AsyncSession, data: CreateProductRequest
    ) -> Product:
        """Create a product with auto-generated slug, translations, and variants.

        The Spanish translation name is used for slug generation.
        Falls back to the first translation if no ES is present.

        If *data.variants* is provided (non-empty list), those variants
        are created.  Otherwise a single default variant (size=None,
        color=None, stock=0) with an auto-generated SKU is created.
        """
        # Determine the source name for slug generation (prefer ES)
        es = next((t for t in data.translations if t.lang == "es"), None)
        name_for_slug = es.name if es else data.translations[0].name
        slug = await self._slug_service.generate_slug(session, name_for_slug)

        product = Product(
            slug=slug,
            price=data.price,
            category_id=data.category_id,
            brand=data.brand,
            condition=(
                ProductCondition(data.condition) if data.condition else None
            ),
            condition_rating=data.condition_rating,
            condition_details=data.condition_details,
            target_gender=data.target_gender,
            material=data.material,
            colors=data.colors,
            trend=data.trend,
            pattern=data.pattern,
            season=data.season,
            cut=data.cut,
            usage=data.usage,
            source_dataset=data.source_dataset,
        )
        session.add(product)

        try:
            await session.flush()
        except IntegrityError as exc:
            if "slug" not in str(exc.orig).lower():
                raise
            slug = await self._slug_service.generate_slug(session, name_for_slug)
            product.slug = slug
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

        # Persist variants via VariantService
        variant_inputs = data.variants
        if variant_inputs and len(variant_inputs) > 0:
            for v in variant_inputs:
                await self._variant_service.create_variant(
                    session, product.id, v
                )
        else:
            # Auto-create default variant
            default_data = ProductVariantCreate(stock=0)
            await self._variant_service.create_variant(
                session, product.id, default_data
            )

        await session.flush()

        # Reload with relationships for the response
        product = await self._reload_product(session, product.id)
        # Invalidate affected caches (best-effort, fire-and-forget).
        event_bus.emit(
            ProductChangedEvent(product_id=product.id, action="created", slug=product.slug)
        )
        return product

    async def update_product(
        self, session: AsyncSession, product_id: UUID, data: UpdateProductRequest
    ) -> Product | None:
        """Partially update a product and optionally upsert translations and variants.

        Returns the updated product or None if not found / soft-deleted.
        """
        product = await self._repo.get_by_id_with_detail(session, product_id)
        if product is None or product.deleted_at is not None:
            return None

        # Scalar fields
        if data.price is not None:
            product.price = data.price
        if data.category_id is not None:
            product.category_id = data.category_id
        if data.brand is not None:
            product.brand = data.brand
        if data.condition is not None:
            product.condition = ProductCondition(data.condition)
        if data.condition_rating is not None:
            product.condition_rating = data.condition_rating
        if data.condition_details is not None:
            product.condition_details = data.condition_details
        if data.target_gender is not None:
            product.target_gender = data.target_gender
        if data.material is not None:
            product.material = data.material
        if data.colors is not None:
            product.colors = data.colors
        if data.trend is not None:
            product.trend = data.trend
        if data.pattern is not None:
            product.pattern = data.pattern
        if data.season is not None:
            product.season = data.season
        if data.cut is not None:
            product.cut = data.cut
        if data.usage is not None:
            product.usage = data.usage
        if data.source_dataset is not None:
            product.source_dataset = data.source_dataset
        if data.image_urls is not None:
            product.image_urls = data.image_urls

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

        # Variants upsert: if variants list is provided, upsert.
        # Existing variants that aren't in the update list are kept as-is.
        if data.variants is not None:
            # Build lookup keyed by (size, color) — existing variants
            existing_variants = [
                v for v in product.variants
                if v.deleted_at is None
            ]
            exist_map: dict[tuple[str | None, str | None], int] = {}
            for ev in existing_variants:
                key = (
                    ev.size.value if hasattr(ev.size, 'value') else ev.size if ev.size else None,
                    ev.color,
                )
                exist_map[key] = ev.id

            for v_data in data.variants:
                size_raw = v_data.size
                size_normalized = size_raw.value if hasattr(size_raw, 'value') else size_raw
                key = (size_normalized, v_data.color)
                existing_id = exist_map.get(key)

                if existing_id is not None:
                    # UPDATE existing variant via VariantService
                    update_data = ProductVariantUpdate(
                        stock=v_data.stock,
                        color_hex=v_data.color_hex,
                        sku=v_data.sku,
                    )
                    await self._variant_service.update_variant(
                        session, existing_id, update_data
                    )
                else:
                    # CREATE new variant via VariantService
                    await self._variant_service.create_variant(
                        session, product.id, v_data
                    )

        await session.flush()
        await session.refresh(product, ["variants"])
        # Refresh reloads from DB without soft-delete filter, so filter manually
        product.variants = [v for v in product.variants if v.deleted_at is None]
        # Invalidate affected caches (best-effort, fire-and-forget).
        event_bus.emit(
            ProductChangedEvent(product_id=product.id, action="updated", slug=product.slug)
        )
        return product

    async def delete_product(
        self, session: AsyncSession, product_id: UUID
    ) -> bool:
        """Soft-delete a product by setting ``deleted_at`` to now.

        Returns ``True`` if a product was deleted, ``False`` if already
        deleted or not found.
        """
        product = await self._repo.find_one(
            session, Product.id == product_id, Product.deleted_at.is_(None)
        )
        if product is None:
            return False

        product.deleted_at = datetime.now(timezone.utc)
        await session.flush()
        # Invalidate affected caches (best-effort, fire-and-forget). The slug
        # is a plain column on the fetched row, so it remains available after
        # the soft-delete flush.
        event_bus.emit(
            ProductChangedEvent(product_id=product.id, action="deleted", slug=product.slug)
        )
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _reload_product(
        self, session: AsyncSession, product_id: UUID
    ) -> Product:
        """Re-fetch a product with eager-loaded relationships."""
        product = await self._repo.get_by_id_with_detail(session, product_id)
        if product is None:
            raise ValueError(f"product {product_id} not found after creation")
        return product
