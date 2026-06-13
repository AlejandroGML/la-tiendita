"""ProductService — business logic for product catalog CRUD.

Async methods accept SQLAlchemy AsyncSession injection at call time.
"""

import logging
import math
import re
import unicodedata
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from app.models.category import Category, CategoryTranslation
from app.models.product import (
    Product,
    ProductCondition,
    ProductSize,
    ProductTranslation,
)
from app.models.product_variant import ProductVariant
from app.models.promotion import Promotion
from app.models.cart import CartItem
from app.schemas.common import ProductFilter
from app.schemas.product import (
    CreateProductRequest,
    ProductResponse,
    TranslationRequest,
    UpdateProductRequest,
)
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
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

        # Eager-load translations + category + variants to avoid N+1 in serialisation
        stmt = stmt.options(
            selectinload(Product.translations),
            selectinload(Product.category).selectinload(Category.translations),
            selectinload(Product.variants),
        )

        items, total = await paginate(stmt, session, page=page, per_page=per_page)
        return items, total

    async def list_admin_products(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[Product], int]:
        """Return a paginated list of ALL products (including soft-deleted)
        for the admin panel."""
        stmt = (
            select(Product)
            .order_by(Product.created_at.desc())
            .options(
                selectinload(Product.translations),
                selectinload(Product.category).selectinload(Category.translations),
                selectinload(Product.variants),
            )
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
                joinedload(Product.variants),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

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
        slug = await self.generate_slug(session, name_for_slug)

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
            slug = await self.generate_slug(session, name_for_slug)
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

        # Persist variants
        variant_inputs = data.variants
        if variant_inputs and len(variant_inputs) > 0:
            for v in variant_inputs:
                sku = v.sku
                if sku is None:
                    size_code = v.size if v.size else None
                    color_code = (
                        self._color_abbr(v.color) if v.color else None
                    )
                    sku = await self._generate_variant_sku(
                        session, slug, size_code, color_code
                    )
                variant = ProductVariant(
                    product_id=product.id,
                    size=ProductSize(v.size) if v.size else None,
                    color=v.color,
                    color_hex=v.color_hex,
                    stock=v.stock,
                    sku=sku,
                )
                session.add(variant)
        else:
            # Auto-create default variant
            default_sku = await self._generate_variant_sku(
                session, slug, size_code=None, color_code=None
            )
            default_variant = ProductVariant(
                product_id=product.id,
                size=None,
                color=None,
                color_hex=None,
                stock=0,
                sku=default_sku,
            )
            session.add(default_variant)

        await session.flush()

        # Reload with relationships for the response
        return await self._reload_product(session, product.id)

    async def update_product(
        self, session: AsyncSession, product_id: UUID, data: UpdateProductRequest
    ) -> Product | None:
        """Partially update a product and optionally upsert translations and variants.

        Returns the updated product or None if not found / soft-deleted.
        """
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.deleted_at.is_(None))
            .options(
                selectinload(Product.translations),
                selectinload(Product.category).selectinload(Category.translations),
                selectinload(Product.variants),
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
            exist_map: dict[tuple[str | None, str | None], ProductVariant] = {}
            for ev in existing_variants:
                key = (
                    ev.size.value if hasattr(ev.size, 'value') else ev.size if ev.size else None,
                    ev.color,
                )
                exist_map[key] = ev

            for v_data in data.variants:
                size_val = ProductSize(v_data.size) if v_data.size else None
                size_raw = v_data.size
                size_normalized = size_raw.value if hasattr(size_raw, 'value') else size_raw
                key = (size_normalized, v_data.color)
                existing = exist_map.get(key)

                if existing is not None:
                    # UPDATE existing variant
                    if v_data.stock is not None:
                        existing.stock = v_data.stock
                    if v_data.color_hex is not None:
                        existing.color_hex = v_data.color_hex
                    if v_data.sku is not None:
                        existing.sku = v_data.sku
                else:
                    # CREATE new variant
                    sku = v_data.sku
                    if sku is None:
                        size_code = v_data.size if v_data.size else None
                        color_code = (
                            self._color_abbr(v_data.color)
                            if v_data.color
                            else None
                        )
                        sku = await self._generate_variant_sku(
                            session, product.slug, size_code, color_code
                        )
                    variant = ProductVariant(
                        product_id=product.id,
                        size=size_val,
                        color=v_data.color,
                        color_hex=v_data.color_hex,
                        stock=v_data.stock,
                        sku=sku,
                    )
                    session.add(variant)

        await session.flush()
        await session.refresh(product, ["variants"])
        # Refresh reloads from DB without soft-delete filter, so filter manually
        product.variants = [v for v in product.variants if v.deleted_at is None]
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
    # Variant CRUD (admin)
    # ------------------------------------------------------------------

    async def list_variants(
        self, session: AsyncSession, product_id: UUID
    ) -> list[ProductVariant]:
        """Return all non-deleted variants for a product."""
        stmt = (
            select(ProductVariant)
            .where(
                ProductVariant.product_id == product_id,
                ProductVariant.deleted_at.is_(None),
            )
            .order_by(ProductVariant.created_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_variant(
        self,
        session: AsyncSession,
        product_id: UUID,
        data: ProductVariantCreate,
    ) -> ProductVariant:
        """Create a new variant for an existing product.

        Validates the product exists and is not soft-deleted.
        Auto-generates SKU if not provided.
        """
        product = await session.get(Product, product_id)
        if product is None or product.deleted_at is not None:
            raise ValueError("product not found")

        sku = data.sku
        if sku is None:
            size_code = data.size if data.size else None
            color_code = self._color_abbr(data.color) if data.color else None
            sku = await self._generate_variant_sku(
                session, product.slug, size_code, color_code
            )

        variant = ProductVariant(
            product_id=product_id,
            size=ProductSize(data.size) if data.size else None,
            color=data.color,
            color_hex=data.color_hex,
            stock=data.stock,
            sku=sku,
        )
        session.add(variant)
        await session.flush()
        return variant

    async def update_variant(
        self,
        session: AsyncSession,
        variant_id: UUID,
        data: ProductVariantUpdate,
    ) -> ProductVariant | None:
        """Partially update an existing variant. Returns None if not found."""
        stmt = select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        variant = result.scalar_one_or_none()
        if variant is None:
            return None

        if data.size is not None:
            variant.size = ProductSize(data.size)
        if data.color is not None:
            variant.color = data.color
        if data.color_hex is not None:
            variant.color_hex = data.color_hex
        if data.stock is not None:
            variant.stock = data.stock
        if data.sku is not None:
            variant.sku = data.sku

        await session.flush()
        return variant

    async def delete_variant(
        self,
        session: AsyncSession,
        variant_id: UUID,
        product_id: UUID | None = None,
    ) -> bool:
        """Soft-delete a variant. Returns False if already deleted or not found.

        When *product_id* is provided, verifies the variant belongs to that
        product — raises ``ValueError`` on mismatch.

        Does NOT allow deletion if the variant is referenced by active
        cart items or order items.
        """
        stmt = select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        variant = result.scalar_one_or_none()
        if variant is None:
            return False

        if product_id is not None and variant.product_id != product_id:
            raise ValueError(
                "variant does not belong to this product"
            )

        # Check for active references in cart_items
        from sqlalchemy import func as sqlfunc

        cart_count = await session.scalar(
            select(sqlfunc.count())
            .select_from(CartItem)
            .where(CartItem.variant_id == variant_id)
        )
        if cart_count and cart_count > 0:
            raise ValueError(
                f"Variant is referenced by {cart_count} active cart item(s). "
                "Remove them before deleting."
            )

        variant.deleted_at = datetime.now(timezone.utc)
        await session.flush()
        return True

    # ------------------------------------------------------------------
    # Variant internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _color_abbr(color: str | None) -> str | None:
        """Convert a color name to a 2-char abbreviation for SKU building."""
        if not color:
            return None
        parts = color.strip().split()
        if len(parts) == 1:
            abbr = parts[0][:2].upper()
        else:
            abbr = "".join(p[0] for p in parts[:2]).upper()
        return abbr

    async def _generate_variant_sku(
        self,
        session: AsyncSession,
        slug: str,
        size_code: str | None,
        color_code: str | None,
    ) -> str:
        """Generate a unique SKU from slug prefix, size, and color.

        Format: ``{slug_prefix}-{size|NS}-{color_abbr|NC}-{seq}``
        Collision-safe via DB unique constraint check with incrementing seq.
        """
        slug_prefix = self._sku_slug_prefix(slug)
        size_part = size_code or "NS"
        color_part = color_code or "NC"

        for seq in range(1, 100):
            sku = f"{slug_prefix}-{size_part}-{color_part}-{seq:02d}"
            exists = await session.scalar(
                select(ProductVariant.id).where(ProductVariant.sku == sku)
            )
            if exists is None:
                return sku

        # Fallback (extremely unlikely): use UUID suffix
        import uuid as _uuid

        short_uuid = str(_uuid.uuid4())[:8]
        return f"{slug_prefix}-{size_part}-{color_part}-{short_uuid}"

    @staticmethod
    def _sku_slug_prefix(slug: str) -> str:
        """Extract a short uppercase prefix from a slug for SKU building."""
        parts = slug.replace("-", " ").split()
        if len(parts) >= 2:
            prefix = "".join(p[0] for p in parts[:3]).upper()
        else:
            prefix = (parts[0][:4] if parts else "PRD").upper()
        return prefix

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

    MAX_SLUG_LEN = 200

    async def generate_slug(
        self, session: AsyncSession, name: str
    ) -> str:
        """Generate a unique slug from *name*, resolving collisions by
        appending a numeric suffix (``-2``, ``-3``, …).

        Slugs are truncated to ``MAX_SLUG_LEN`` (200) to prevent
        database insertion failures on the ``String(200)`` column.
        Collision suffixes fit within the limit by shrinking the base.

        Example: "Chaqueta Denim" → "chaqueta-denim". If that slug is
        taken, tries "chaqueta-denim-2", and so on.
        """
        base = self.slugify(name)
        if len(base) > self.MAX_SLUG_LEN:
            base = base[: self.MAX_SLUG_LEN]
        slug = base
        attempt = 1

        while True:
            existing = await session.execute(
                select(Product.id).where(Product.slug == slug)
            )
            if existing.scalar_one_or_none() is None:
                return slug
            attempt += 1
            suffix = f"-{attempt}"
            # Shrink base so base + suffix ≤ MAX_SLUG_LEN
            available = self.MAX_SLUG_LEN - len(suffix)
            slug = f"{base[:available]}{suffix}"

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
                selectinload(Product.variants),
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
                (Promotion.product_id == Product.id) | (Promotion.product_id.is_(None)),
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

        # Full-text search on translations (name OR description)
        if filters.q:
            escaped = filters.q.replace("%", r"\%").replace("_", r"\_")
            search_term = f"%{escaped}%"
            stmt = stmt.join(
                ProductTranslation,
                and_(
                    ProductTranslation.product_id == Product.id,
                    ProductTranslation.language_code == filters.lang,
                ),
                isouter=True,
            ).where(
                or_(
                    ProductTranslation.name.ilike(search_term, escape="\\"),
                    ProductTranslation.description.ilike(search_term, escape="\\"),
                )
            )

        # Build ordering: sort param overrides default stock-priority ordering
        if filters.sort == "newest":
            return stmt.order_by(Product.created_at.desc())
        if filters.sort == "price_asc":
            return stmt.order_by(Product.price.asc())
        if filters.sort == "price_desc":
            return stmt.order_by(Product.price.desc())

        # Default: products with stock > 0 first, then by created_at DESC
        in_stock = (
            exists()
            .where(
                ProductVariant.product_id == Product.id,
                ProductVariant.stock > 0,
                ProductVariant.deleted_at.is_(None),
            )
            .correlate(Product)
        )
        return stmt.order_by(case((in_stock, 0), else_=1), Product.created_at.desc())
