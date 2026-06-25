"""ProductController (public) + AdminProductController (guarded).

ProductController: public catalog — no auth required.
AdminProductController: admin CRUD with ``guards=[admin_guard]`` (JWT via middleware).
"""

import math
from uuid import UUID

from litestar import Controller, get, post, put, delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException, ValidationException
from litestar.response import Redirect
from pydantic import ValidationError as PydanticValidationError

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.guards.admin_guard import admin_guard
from app.repositories.product_repository import ProductRepository
from app.schemas.common import ProductFilter
from app.schemas.product import (
    CreateProductRequest,
    ProductResponse,
    TranslationRequest,
    UpdateProductRequest,
)
from app.services.product_service import ProductService
from app.serializers.product import build_product_response


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_product_service() -> ProductService:
    return ProductService()


async def provide_product_repository() -> ProductRepository:
    return ProductRepository()


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


class ProductController(Controller):
    """Public product catalog — no authentication required."""

    path = "/api/products"
    tags = ["products"]
    dependencies = {
        "service": Provide(provide_product_service, sync_to_thread=False),
        "repo": Provide(provide_product_repository, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/")
    async def list_products(
        self,
        service: ProductService,
        session: AsyncSession,
        lang: str = "es",
        page: int = 1,
        per_page: int = 12,
        search: str | None = None,
        category_id: int | None = None,
        size: str | None = None,
        condition: str | None = None,
        condition_rating: int | None = None,
        brand: str | None = None,
        target_gender: str | None = None,
        material: str | None = None,
        trend: str | None = None,
        pattern: str | None = None,
        season: str | None = None,
        usage: str | None = None,
        min_price: str | None = None,
        max_price: str | None = None,
        has_promotion: bool | None = None,
        sort: str | None = None,
    ) -> dict:
        """Paginated product listing with search, filter, and i18n.

        Query params: ``?lang=``, ``?page=``, ``?per_page=``, ``?search=``,
        ``?category_id=``, ``?size=``, ``?condition=``, ``?condition_rating=``,
        ``?brand=``, ``?target_gender=``, ``?material=``, ``?trend=``,
        ``?pattern=``, ``?season=``, ``?usage=``, ``?min_price=``,
        ``?max_price=``, ``?has_promotion=``, ``?sort=``.
        """
        from decimal import Decimal

        try:
            filters = ProductFilter(
                lang=lang,
                page=page,
                per_page=per_page,
                q=search,
                category=category_id,
                size=size,
                condition=condition,
                condition_rating=condition_rating,
                brand=brand,
                target_gender=target_gender,
                material=material,
                trend=trend,
                pattern=pattern,
                season=season,
                usage=usage,
                min_price=Decimal(min_price) if min_price is not None else None,
                max_price=Decimal(max_price) if max_price is not None else None,
                has_promotion=has_promotion,
                sort=sort,
            )
        except (PydanticValidationError, ValueError) as exc:
            raise ValidationException(detail=str(exc))

        items, total = await service.list_products(session, filters)

        # Resolve active promotions for sale pricing
        promotions = await service._apply_promotions(session, items)

        per_page = filters.per_page
        total_pages = max(1, math.ceil(total / per_page))

        data = [
            build_product_response(p, lang=filters.lang, promotion_info=promotions)
            for p in items
        ]

        return {
            "data": data,
            "pagination": {
                "page": filters.page,
                "per_page": per_page,
                "total": total,
                "pages": total_pages,
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

    @get("/{identifier:str}")
    async def get_product(
        self,
        identifier: str,
        service: ProductService,
        repo: ProductRepository,
        session: AsyncSession,
    ) -> dict:
        """Product detail by slug. If *identifier* is a UUID, redirect
        (307) to the slug-based URL."""
        # Slug redirect: if the identifier looks like a UUID, resolve by ID
        try:
            product_id = UUID(identifier)
        except ValueError:
            # Not a UUID — treat as slug
            product = await service.get_product_by_slug(session, identifier)
        else:
            # Resolve by ID first, then redirect to slug
            product = await repo.get_by_id_for_resolve(session, product_id)
            if product is not None:
                return Redirect(
                    path=f"/api/products/{product.slug}",
                    status_code=307,
                )

        if product is None:
            raise NotFoundException(detail="product not found")

        promotions = await service._apply_promotions(session, [product])
        return build_product_response(product, promotion_info=promotions)


# ---------------------------------------------------------------------------
# Admin controller
# ---------------------------------------------------------------------------


class AdminProductController(Controller):
    """Admin product CRUD — JWT + admin role required."""

    path = "/api/admin/products"
    tags = ["admin-products"]
    guards = [admin_guard]
    dependencies = {
        "service": Provide(provide_product_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/", status_code=200)
    async def list_admin_products(
        self,
        service: ProductService,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        """List all products for the admin panel (paginated)."""
        items, total = await service.list_admin_products(
            session, page=page, per_page=per_page
        )
        return {
            "data": [build_product_response(item) for item in items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": max(1, math.ceil(total / per_page)),
            },
        }

    @post("/", status_code=201)
    async def create_product(
        self,
        data: CreateProductRequest,
        service: ProductService,
        session: AsyncSession,
    ) -> dict:
        """Create a product with auto-generated slug from Spanish name.

        Requires at least one translation.
        """
        try:
            product = await service.create_product(session, data)
        except ValueError as exc:
            raise ValidationException(detail=str(exc)) from exc

        return build_product_response(product)

    @put("/{product_id:uuid}", status_code=200)
    async def update_product(
        self,
        product_id: UUID,
        data: UpdateProductRequest,
        service: ProductService,
        session: AsyncSession,
    ) -> dict:
        """Update a product and optionally upsert translations."""
        product = await service.update_product(session, product_id, data)
        if product is None:
            raise NotFoundException(detail="product not found")
        return build_product_response(product)

    @delete("/{product_id:uuid}", status_code=204)
    async def delete_product(
        self,
        product_id: UUID,
        service: ProductService,
        session: AsyncSession,
    ) -> None:
        """Soft-delete a product (sets ``deleted_at``)."""
        deleted = await service.delete_product(session, product_id)
        if not deleted:
            raise NotFoundException(detail="product not found")
