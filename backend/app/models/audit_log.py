"""AuditLog ORM model — admin action audit trail.

Each row captures a single admin mutation: who did what to which entity,
when, and from which IP address.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class AuditLog(Base):
    """Immutable audit record of an admin mutation.

    Attributes:
        actor_id: FK to the admin user who performed the action.
        action: Dot-notation action string (e.g. ``product.create``).
        entity_type: The kind of entity mutated (product, variant, etc.).
        entity_id: The string form of the entity's primary key.
        details: Optional JSONB mutation context (old/new values, slug, etc.).
        ip_address: Optional client IP address of the admin.
        created_at: Server-side timestamp of when the action occurred.
    """

    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    entity_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    details: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
