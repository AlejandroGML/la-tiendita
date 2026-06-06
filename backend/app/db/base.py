"""Declarative bases for all SQLAlchemy models.

``Base`` provides a UUID primary key. ``TranslationBase`` shares the same
metadata registry but does NOT include a PK column — intended for tables
with composite primary keys (e.g., ``(entity_id, language_code)``).
"""

import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

_registry = registry()


class Base(DeclarativeBase):
    """Base class for ORM models with a shared UUID primary key."""

    registry = _registry

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class TranslationBase(DeclarativeBase):
    """Base for composite-PK models — no auto-generated primary key.

    Shares the same metadata registry as ``Base`` so Alembic autogenerate
    discovers all tables regardless of which base they inherit from.
    """

    registry = _registry
