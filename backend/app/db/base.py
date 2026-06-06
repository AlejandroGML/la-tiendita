"""Declarative base for all SQLAlchemy models.

Every model inherits from Base and automatically gets a UUID primary key.
"""

import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models with a shared UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
