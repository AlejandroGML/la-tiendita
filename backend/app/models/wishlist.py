"""Wishlist bridge ORM model — composite PK (user_id, product_id).

Wishlist intentionally does NOT inherit from ``Base`` because it uses
a composite primary key instead of the UUID surrogate key provided by Base.
It still shares the same metadata registry so Alembic discovers the table.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import _registry

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class _CompositeBase(DeclarativeBase):
    """Base for models with composite PKs — no auto-generated id column.

    Shares the same metadata registry as Base so Alembic discovers all tables.
    """
    registry = _registry


class Wishlist(_CompositeBase):
    """A user's wishlist / favorites entry.

    Uses composite primary key (user_id, product_id) — no surrogate key.
    Follows the same pattern as CartItem but without quantity logic.
    """

    __tablename__ = "wishlist"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "product_id", name="pk_wishlist"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    product: Mapped["Product"] = relationship("Product")
