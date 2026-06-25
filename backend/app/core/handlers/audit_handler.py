"""AuditHandler — subscribes to AuditEvent and persists via AuditService.

Pattern: identical to :class:`EmailHandler`.  Opens its **own** ``AsyncSession``
via the global session factory so audit persistence is fully decoupled from the
request lifecycle.  The event bus runs each handler as a fire-and-forget
``asyncio.Task`` — handler failure never blocks the HTTP response.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_bus import EventBus
from app.core.events import AuditEvent
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuditHandler:
    """Subscribes to :class:`AuditEvent` and persists ``AuditLog`` rows.

    Usage (wired in ``app/main.py`` during startup)::

        AuditHandler(event_bus=event_bus, session_factory=async_session)
    """

    def __init__(
        self,
        event_bus: EventBus,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._audit_service = AuditService()
        self._session_factory = session_factory

        event_bus.subscribe(AuditEvent, self._handle_audit)

        logger.info("AuditHandler registered for AuditEvent")

    async def _handle_audit(self, event: AuditEvent) -> None:
        """Persist an AuditLog row in a fresh DB session."""
        async with self._session_factory() as session:
            await self._audit_service.create_audit_log(session, event)
            try:
                await session.commit()
            except Exception:
                logger.exception("Failed to commit audit log entry")
