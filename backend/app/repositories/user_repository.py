"""UserRepository — encapsulates user data access.

Moves SQLAlchemy queries out of ``AuthService`` and ``ProfileController``
into a dedicated data-access layer.  The service retains password hashing,
token creation, TOTP verification — all authentication business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User-specific data access — email lookup, role queries.

    Usage::

        repo = UserRepository()
        user = await repo.get_by_email(session, "xoko@example.com")
        admins = await repo.get_with_role(session, UserRole.ADMIN)
    """

    def __init__(self) -> None:
        super().__init__(User)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        """Fetch a user by their email address.

        Args:
            session: Active async DB session.
            email: The user's email.

        Returns:
            The user or ``None``.
        """
        return await self.find_one(session, User.email == email)

    async def get_with_role(
        self,
        session: AsyncSession,
        role: UserRole,
    ) -> list[User]:
        """Return all users with a given role.

        Args:
            session: Active async DB session.
            role: The ``UserRole`` to filter by.

        Returns:
            List of matching users.
        """
        return await self.find_all(session, User.role == role)

    async def get_all_with_order_counts(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[tuple], int]:
        """Return paginated users with their order counts via scalar subquery."""
        from sqlalchemy import func, select
        from app.models.order import Order

        total = await self.count(session)

        order_count_sq = (
            select(
                Order.user_id,
                func.count(Order.id).label("orders_count"),
            )
            .group_by(Order.user_id)
            .subquery()
        )

        offset = (page - 1) * per_page
        stmt = (
            select(
                User,
                func.coalesce(order_count_sq.c.orders_count, 0).label("orders_count"),
            )
            .outerjoin(order_count_sq, User.id == order_count_sq.c.user_id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        return list(result.all()), total
