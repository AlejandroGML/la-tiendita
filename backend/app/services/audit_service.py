"""AuditService — persists AuditLog rows from AuditEvent instances.

Called by :class:`AuditHandler` inside a fresh DB session so audit
persistence is decoupled from the request lifecycle.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import AuditEvent
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class AuditService:
    """Translates :class:`AuditEvent` → :class:`AuditLog` and persists it.

    The ``audit_repo`` parameter enables test injection of a mock repository.
    """

    def __init__(
        self, audit_repo: AuditRepository | None = None
    ) -> None:
        self._repo = audit_repo or AuditRepository()

    async def create_audit_log(
        self,
        session: AsyncSession,
        event: AuditEvent,
    ) -> AuditLog:
        """Create and flush an ``AuditLog`` row from an ``AuditEvent``.

        Args:
            session: Active async DB session.
            event:   The domain event carrying audit data.

        Returns:
            The flushed ``AuditLog`` instance.
        """
        audit_log = AuditLog(
            actor_id=event.actor_id,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            details=event.details,
            ip_address=event.ip_address,
        )
        return await self._repo.add(session, audit_log)
