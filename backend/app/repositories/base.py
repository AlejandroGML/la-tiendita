"""Base repository with common CRUD operations.

All repository methods receive the async session as a parameter — they are
stateless, injectable, and DI-friendly. Subclass ``BaseRepository[ModelT]``
for model-specific repositories and add query methods there.
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic repository with common database access operations.

    Usage::

        class ProductRepository(BaseRepository[Product]):
            def __init__(self) -> None:
                super().__init__(Product)
    """

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    # ------------------------------------------------------------------
    # Single-instance lookups
    # ------------------------------------------------------------------

    async def get_by_id(
        self,
        session: AsyncSession,
        id: Any,
        *,
        options: list | None = None,
    ) -> ModelT | None:
        """Fetch a single instance by primary key.

        Args:
            session: Active async DB session.
            id: Primary key value.
            options: Optional list of SQLAlchemy loader options
                     (e.g. ``[selectinload(Model.relation)]``).

        Returns:
            The model instance or ``None`` if not found.
        """
        stmt = select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        if options:
            stmt = stmt.options(*options)
        return await session.scalar(stmt)

    async def find_one(
        self,
        session: AsyncSession,
        *where: Any,
        options: list | None = None,
        order_by: Any | None = None,
    ) -> ModelT | None:
        """Find a single instance matching all ``where`` clauses.

        Args:
            session: Active async DB session.
            where: Zero or more SQLAlchemy filter expressions.
            options: Optional eager-load options.
            order_by: Optional ordering expression.

        Returns:
            The first matching instance or ``None``.
        """
        stmt = select(self.model).where(*where)
        if options:
            stmt = stmt.options(*options)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return await session.scalar(stmt)

    # ------------------------------------------------------------------
    # Multi-instance lookups
    # ------------------------------------------------------------------

    async def find_all(
        self,
        session: AsyncSession,
        *where: Any,
        options: list | None = None,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        """Find all instances matching ``where`` clauses.

        Args:
            session: Active async DB session.
            where: Zero or more SQLAlchemy filter expressions.
            options: Optional eager-load options.
            order_by: Optional ordering expression.

        Returns:
            A list of matching instances (empty if none found).
        """
        stmt = select(self.model).where(*where)
        if options:
            stmt = stmt.options(*options)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_paginated(
        self,
        session: AsyncSession,
        *,
        stmt: Select | None = None,
        page: int = 1,
        per_page: int = 12,
    ) -> tuple[list[ModelT], int]:
        """Execute a paginated query with total count.

        Uses the existing ``paginate`` utility for consistent count + offset
        fetch.  When ``stmt`` is ``None``, selects all rows of ``self.model``.

        Args:
            session: Active async DB session.
            stmt: A ``select()`` statement (with filters, joins, options).
                  If ``None``, defaults to ``select(self.model)``.
            page: 1-indexed page number.
            per_page: Results per page.

        Returns:
            ``(items, total_count)`` — compatible with ``paginate()``.
        """
        from app.utils.pagination import paginate

        query = stmt if stmt is not None else select(self.model)
        return await paginate(query, session, page=page, per_page=per_page)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    async def add(self, session: AsyncSession, instance: ModelT) -> ModelT:
        """Add a new instance to the session and flush.

        Args:
            session: Active async DB session.
            instance: The model instance to persist.

        Returns:
            The flushed instance (with generated PK / defaults populated).
        """
        session.add(instance)
        await session.flush()
        return instance

    async def delete(self, session: AsyncSession, instance: ModelT) -> None:
        """Delete an instance from the session and flush.

        Args:
            session: Active async DB session.
            instance: The model instance to remove.
        """
        await session.delete(instance)
        await session.flush()

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    async def count(
        self,
        session: AsyncSession,
        *where: Any,
    ) -> int:
        """Count instances matching ``where`` clauses.

        Args:
            session: Active async DB session.
            where: Zero or more SQLAlchemy filter expressions.

        Returns:
            The total count of matching rows.
        """
        stmt = select(func.count()).select_from(self.model)
        if where:
            stmt = stmt.where(*where)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def exists(
        self,
        session: AsyncSession,
        *where: Any,
    ) -> bool:
        """Check whether at least one instance matches ``where`` clauses.

        More efficient than ``count() > 0`` because it uses ``LIMIT 1``.

        Args:
            session: Active async DB session.
            where: Zero or more SQLAlchemy filter expressions.

        Returns:
            ``True`` if at least one matching row exists.
        """
        stmt = select(self.model.id).where(*where).limit(1)  # type: ignore[attr-defined]
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
