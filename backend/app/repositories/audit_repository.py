"""AuditRepository — thin data-access layer for AuditLog persistence.

Inherits ``add()``, ``get_by_id()``, ``count()``, and all other CRUD
operations from :class:`BaseRepository`.  No custom query methods needed
for the current audit scope.
"""

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
