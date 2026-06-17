"""CategoryRepository — encapsulates category data access.

Moves inline SQLAlchemy queries from ``CategoryController`` and
``AdminCategoryController`` into a dedicated data-access layer.
Category uses a SERIAL integer PK (unlike UUIDs for other models).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Category-specific data access — slug lookups, translation loading.

    Usage::

        repo = CategoryRepository()
        categories = await repo.list_all_with_translations(session)
        category = await repo.get_by_slug(session, "ropa-de-mujer")
    """

    def __init__(self) -> None:
        super().__init__(Category)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_by_slug(
        self,
        session: AsyncSession,
        slug: str,
    ) -> Category | None:
        """Fetch a category by slug with translations eager-loaded.

        Args:
            session: Active async DB session.
            slug: The category slug.

        Returns:
            The category or ``None``.
        """
        return await self.find_one(
            session,
            Category.slug == slug,
            options=[selectinload(Category.translations)],
        )

    async def list_all_with_translations(
        self,
        session: AsyncSession,
    ) -> list[Category]:
        """Return all categories ordered by id with translations loaded.

        Args:
            session: Active async DB session.

        Returns:
            List of all categories.
        """
        return await self.find_all(
            session,
            options=[selectinload(Category.translations)],
            order_by=Category.id,
        )

    async def slug_exists(
        self,
        session: AsyncSession,
        slug: str,
    ) -> bool:
        """Check whether a category slug is already taken.

        Args:
            session: Active async DB session.
            slug: The slug to check.

        Returns:
            ``True`` if the slug exists.
        """
        return await self.exists(session, Category.slug == slug)
