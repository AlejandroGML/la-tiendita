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
