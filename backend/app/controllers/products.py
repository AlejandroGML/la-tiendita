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
from app.schemas.common import ProductFilter
from app.schemas.product import (
    CreateProductRequest,
    ProductResponse,
    TranslationRequest,
    UpdateProductRequest,
)
from app.services.product_service import ProductService


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_product_service() -> ProductService:
    return ProductService()


async def provide_session() -> AsyncSession:
    async with _async_session_fn() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_product_response(product, *, lang: str | None = None) -> dict:
    """Convert a Product ORM instance to a dict, optionally filtering
    translations to *lang* with ``en`` fallback."""
    translations = [
        {
            "language_code": t.language_code,
            "name": t.name,
            "description": t.description,
        }
        for t in product.translations
    ]

    if lang is not None:
        # Find translation for requested lang, fallback to en, then first
        matched = next(
            (t for t in translations if t["language_code"] == lang), None
        )
        if matched is None:
            matched = next(
                (t for t in translations if t["language_code"] == "en"), None
            )
        if matched is None and translations:
            matched = translations[0]
        translations = [matched] if matched else []

    return {
        "id": str(product.id),
        "slug": product.slug,
        "price": str(product.price),
        "category_id": product.category_id,
        "size": product.size.value if product.size else None,
        "brand": product.brand,
        "condition": product.condition.value if product.condition else None,
        "image_urls": product.image_urls,
        "stock": product.stock,
        "translations": translations,
        "created_at": product.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Public controller
# ---------------------------------------------------------------------------


class ProductController(Controller):
    """Public product catalog — no authentication required."""

    path = "/api/products"
    tags = ["products"]
    dependencies = {
        "service": Provide(provide_product_service, sync_to_thread=False),
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
        min_price: str | None = None,
        max_price: str | None = None,
    ) -> dict:
        """Paginated product listing with search, filter, and i18n.

        Query params: ``?lang=``, ``?page=``, ``?per_page=``, ``?search=``,
        ``?category_id=``, ``?size=``, ``?condition=``, ``?min_price=``,
        ``?max_price=``.
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
                min_price=Decimal(min_price) if min_price is not None else None,
                max_price=Decimal(max_price) if max_price is not None else None,
            )
        except (PydanticValidationError, ValueError) as exc:
            raise ValidationException(detail=str(exc))

        items, total = await service.list_products(session, filters)

        per_page = filters.per_page
        total_pages = max(1, math.ceil(total / per_page))

        data = [
            _build_product_response(p, lang=filters.lang) for p in items
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
                "min_price": str(filters.min_price) if filters.min_price else None,
                "max_price": str(filters.max_price) if filters.max_price else None,
                "search": filters.q,
            },
        }

    @get("/{identifier:str}")
    async def get_product(
        self,
        identifier: str,
        service: ProductService,
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
            from sqlalchemy import select
            from app.models.product import Product

            result = await session.execute(
                select(Product).where(
                    Product.id == product_id, Product.deleted_at.is_(None)
                )
            )
            product = result.scalar_one_or_none()
            if product is not None:
                return Redirect(
                    path=f"/api/products/{product.slug}",
                    status_code=307,
                )

        if product is None:
            raise NotFoundException(detail="product not found")

        return _build_product_response(product)


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

        return _build_product_response(product)

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
        return _build_product_response(product)

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
