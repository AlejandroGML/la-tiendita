"""CartItem ORM model — dual-scope shopping cart (user or guest session)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.product_variant import ProductVariant
    from app.models.user import User


class CartItem(Base):
    """A product line in a shopping cart — scoped to either a registered
    user OR an anonymous guest session, never both.

    Scope is enforced by a XOR CHECK constraint: exactly one of
    ``user_id`` or ``session_id`` must be non-null.

    Identity uses four partial unique indexes — two per scope — so the
    same product can exist independently in a user cart and a guest cart:
    - user + product (no variant)
    - user + variant
    - session + product (no variant)
    - session + variant

    Duplicate adds increment quantity instead of inserting a new row.
    """

    __tablename__ = "cart_items"
    __table_args__ = (
        Index(
            "uq_cart_user_product",
            "user_id",
            "product_id",
            unique=True,
            postgresql_where=text(
                "user_id IS NOT NULL AND variant_id IS NULL"
            ),
        ),
        Index(
            "uq_cart_user_variant",
            "user_id",
            "variant_id",
            unique=True,
            postgresql_where=text(
                "user_id IS NOT NULL AND variant_id IS NOT NULL"
            ),
        ),
        Index(
            "uq_cart_session_product",
            "session_id",
            "product_id",
            unique=True,
            postgresql_where=text(
                "session_id IS NOT NULL AND variant_id IS NULL"
            ),
        ),
        Index(
            "uq_cart_session_variant",
            "session_id",
            "variant_id",
            unique=True,
            postgresql_where=text(
                "session_id IS NOT NULL AND variant_id IS NOT NULL"
            ),
        ),
        CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
        CheckConstraint(
            "(user_id IS NOT NULL AND session_id IS NULL)"
            " OR (user_id IS NULL AND session_id IS NOT NULL)",
            name="ck_cart_xor_scope",
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_variants.id"), nullable=True, index=True
    )
    size: Mapped[str | None] = mapped_column(String(10), nullable=True)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User | None"] = relationship("User")
    product: Mapped["Product"] = relationship("Product")
    variant: Mapped["ProductVariant | None"] = relationship("ProductVariant")
