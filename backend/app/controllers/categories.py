"""CategoryController (public) + AdminCategoryController (guarded).

CategoryController: public catalog — no auth required.
AdminCategoryController: admin CRUD with ``guards=[jwt_auth, admin_guard]``.

Data access is delegated to ``CategoryRepository`` — controllers only
handle HTTP concerns (request parsing, response building, error mapping).
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

from app.db.engine import async_session as _async_session_fn
from app.guards.admin_guard import admin_guard
from app.models.category import Category, CategoryTranslation
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CreateCategoryRequest
from app.serializers.category import (
    build_category_response,
    build_category_list_item,
)


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_category_repository() -> CategoryRepository:
    return CategoryRepository()


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


class CategoryController(Controller):
    """Public category listing — no authentication required."""

    path = "/api/categories"
    tags = ["categories"]
    dependencies = {
        "repo": Provide(provide_category_repository, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/")
    async def list_categories(
        self,
        repo: CategoryRepository,
        lang: str = "es",
        session: AsyncSession = None,
    ) -> list[dict]:
        """List all categories with translated name per ``?lang=``."""
        categories = await repo.list_all_with_translations(session)
        return [build_category_list_item(c, lang) for c in categories]


# ---------------------------------------------------------------------------
# Admin controller
# ---------------------------------------------------------------------------


class AdminCategoryController(Controller):
    """Admin category CRUD — JWT + admin role required."""

    path = "/api/admin/categories"
    tags = ["admin-categories"]
    guards = [admin_guard]
    dependencies = {
        "repo": Provide(provide_category_repository, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @post("/", status_code=201)
    async def create_category(
        self,
        data: CreateCategoryRequest,
        repo: CategoryRepository,
        session: AsyncSession,
    ) -> dict:
        """Create a category with translations."""
        # Check slug uniqueness
        if await repo.slug_exists(session, data.slug):
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
        result = await repo.get_by_id(
            session, category.id, options=[Category.translations]
        )
        if result is None:
            raise HTTPException(status_code=500, detail="category not found after creation")
        return build_category_response(result)

    @put("/{category_id:int}", status_code=200)
    async def update_category(
        self,
        category_id: int,
        data: CreateCategoryRequest,
        repo: CategoryRepository,
        session: AsyncSession,
    ) -> dict:
        """Update a category and its translations (upsert)."""
        category = await repo.get_by_id(
            session, category_id, options=[Category.translations]
        )
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
        return build_category_response(category)

    @delete("/{category_id:int}", status_code=204)
    async def delete_category(
        self,
        category_id: int,
        repo: CategoryRepository,
        session: AsyncSession,
    ) -> None:
        """Hard-delete a category. Fails with 409 if products are linked."""
        # Check for associated products
        product_count = await repo.count_products(session, category_id)
        if product_count > 0:
            raise HTTPException(
                status_code=409,
                detail="category has associated products",
            )

        category = await repo.get_by_id(session, category_id)
        if category is None:
            raise NotFoundException(detail="category not found")

        await session.delete(category)
        await session.flush()
