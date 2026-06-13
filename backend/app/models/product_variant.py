"""ProductVariant ORM model — size × color × stock × SKU child of Product."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.product import ProductSize

if TYPE_CHECKING:
    from app.models.product import Product


class ProductVariant(Base):
    """A specific size+color combination of a product with its own stock and SKU.

    Each Product has one or more variants.  A variant without size/color
    is the "default variant" used for products that don't offer choices.
    Soft-delete via ``deleted_at`` supports per-variant removal while
    preserving cart/order history.
    """

    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    size: Mapped[ProductSize | None] = mapped_column(
        Enum(ProductSize, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color_hex: Mapped[str | None] = mapped_column(
        String(7), nullable=True, comment="CSS hex e.g. #FF5733"
    )
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product", back_populates="variants"
    )
