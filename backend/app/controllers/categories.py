"""CategoryController (public) + AdminCategoryController (guarded).

CategoryController: public catalog — no auth required.
AdminCategoryController: admin CRUD with ``guards=[jwt_auth, admin_guard]``.
"""

from litestar import Controller, get, post, put, delete
from litestar.di import Provide
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    ValidationException,
)

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.engine import async_session as _async_session_fn
from app.guards.admin_guard import admin_guard
from app.models.category import Category, CategoryTranslation
from app.models.product import Product
from app.schemas.category import CreateCategoryRequest


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


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


def _build_category_response(category: Category) -> dict:
    """Convert a Category ORM instance to a full response dict with all
    translations."""
    return {
        "id": category.id,
        "slug": category.slug,
        "image_url": category.image_url,
        "translations": [
            {
                "language_code": t.language_code,
                "name": t.name,
            }
            for t in category.translations
        ],
    }


def _build_category_list_item(category: Category, lang: str) -> dict:
    """Convert a Category to a list-item dict with translated name.

    Falls back to ``en``, then the first available translation if the
    requested language is missing."""
    translations = {
        t.language_code: t.name for t in category.translations
    }
    name = translations.get(lang) or translations.get("en")
    if name is None and translations:
        name = next(iter(translations.values()))

    return {
        "id": category.id,
        "slug": category.slug,
        "name": name or "",
    }


# ---------------------------------------------------------------------------
# Public controller
# ---------------------------------------------------------------------------


class CategoryController(Controller):
    """Public category listing — no authentication required."""

    path = "/api/categories"
    tags = ["categories"]
    dependencies = {
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/")
    async def list_categories(
        self,
        lang: str = "es",
        session: AsyncSession = None,
    ) -> list[dict]:
        """List all categories with translated name per ``?lang=``."""
        stmt = (
            select(Category)
            .options(selectinload(Category.translations))
            .order_by(Category.id)
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()

        return [_build_category_list_item(c, lang) for c in categories]


# ---------------------------------------------------------------------------
# Admin controller
# ---------------------------------------------------------------------------


class AdminCategoryController(Controller):
    """Admin category CRUD — JWT + admin role required."""

    path = "/api/admin/categories"
    tags = ["admin-categories"]
    guards = [admin_guard]
    dependencies = {
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @post("/", status_code=201)
    async def create_category(
        self,
        data: CreateCategoryRequest,
        session: AsyncSession,
    ) -> dict:
        """Create a category with translations."""
        # Check slug uniqueness
        existing = await session.execute(
            select(Category.id).where(Category.slug == data.slug)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail=f"category slug '{data.slug}' already exists",
            )

        category = Category(
            slug=data.slug,
            image_url=data.image_url,
        )
        session.add(category)
        await session.flush()

        for t in data.translations:
            ct = CategoryTranslation(
                category_id=category.id,
                language_code=t.lang,
                name=t.name,
            )
            session.add(ct)

        await session.flush()

        # Reload with translations
        stmt = (
            select(Category)
            .where(Category.id == category.id)
            .options(selectinload(Category.translations))
        )
        result = await session.execute(stmt)
        return _build_category_response(result.scalar_one())

    @put("/{category_id:int}", status_code=200)
    async def update_category(
        self,
        category_id: int,
        data: CreateCategoryRequest,
        session: AsyncSession,
    ) -> dict:
        """Update a category and its translations (upsert)."""
        stmt = (
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.translations))
        )
        result = await session.execute(stmt)
        category = result.scalar_one_or_none()
        if category is None:
            raise NotFoundException(detail="category not found")

        # Scalar fields
        category.slug = data.slug
        category.image_url = data.image_url

        # Translations upsert
        existing_map = {t.language_code: t for t in category.translations}
        for t in data.translations:
            if t.lang in existing_map:
                existing_map[t.lang].name = t.name
            else:
                ct = CategoryTranslation(
                    category_id=category.id,
                    language_code=t.lang,
                    name=t.name,
                )
                session.add(ct)

        await session.flush()
        return _build_category_response(category)

    @delete("/{category_id:int}", status_code=204)
    async def delete_category(
        self,
        category_id: int,
        session: AsyncSession,
    ) -> None:
        """Hard-delete a category. Fails with 409 if products are linked."""
        # Check for associated products
        product_count = await session.execute(
            select(func.count(Product.id)).where(
                Product.category_id == category_id,
                Product.deleted_at.is_(None),
            )
        )
        if product_count.scalar_one() > 0:
            raise HTTPException(
                status_code=409,
                detail="category has associated products",
            )

        stmt = select(Category).where(Category.id == category_id)
        result = await session.execute(stmt)
        category = result.scalar_one_or_none()
        if category is None:
            raise NotFoundException(detail="category not found")

        await session.delete(category)
        await session.flush()
