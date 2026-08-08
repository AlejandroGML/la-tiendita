"""AuditRepository — thin data-access layer for AuditLog persistence.

Inherits ``add()``, ``get_by_id()``, ``count()``, and all other CRUD
operations from :class:`BaseRepository`.  Adds actor-scoped deletion
for user teardown.
"""

from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Minimal repository for audit log persistence.

    Usage::

        repo = AuditRepository()
        await repo.add(session, audit_log)
    """

    def __init__(self) -> None:
        super().__init__(AuditLog)

    async def delete_by_actor(
        self,
        session: AsyncSession,
        actor_id: UUID,
    ) -> int:
        """Delete all audit log entries for a given actor.

        Args:
            session: Active async DB session.
            actor_id: The actor UUID.

        Returns:
            The number of deleted rows.
        """
        result = await session.execute(
            delete(AuditLog).where(AuditLog.actor_id == actor_id)
        )
        await session.flush()
        return result.rowcount or 0
