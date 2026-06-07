"""Product and ProductTranslation ORM models with enums."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, TranslationBase

if TYPE_CHECKING:
    from app.models.category import Category


class ProductCondition(StrEnum):
    """Condition rating for second-hand clothing."""

    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"


class ProductSize(StrEnum):
    """Standard EU clothing sizes."""

    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"


class Product(Base):
    """A sellable clothing item with translations and category reference.

    Extended with detailed second-hand condition metadata, material,
    colours, trend/pattern/season, and dataset provenance fields to
    support rich catalogues like HuggingFace fashion-second-hand.
    """

    __tablename__ = "products"

    slug: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    size: Mapped[ProductSize | None] = mapped_column(
        Enum(ProductSize, values_callable=lambda x: [e.value for e in x]), nullable=True
    )
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    condition: Mapped[ProductCondition | None] = mapped_column(
        Enum(ProductCondition, values_callable=lambda x: [e.value for e in x]), nullable=True
    )
    condition_rating: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="1-5 quality rating (dataset condition)"
    )
    condition_details: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Structured defects: {pilling, damage, stains, holes, smell}"
    )
    target_gender: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Ladies, Men, Kids, Unisex"
    )
    material: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="e.g. 95%cotton 5%elastan"
    )
    colors: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, comment="e.g. ['Pink', 'Blue']"
    )
    trend: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="No trend, Sports, 90s, 80s, etc."
    )
    pattern: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Floral print, Striped, Animal print, etc."
    )
    season: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="All, Winter, Summer, Spring, Autumn"
    )
    cut: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, comment="e.g. ['Collar', 'V-collar', 'Cropped']"
    )
    usage: Mapped[str | None] = mapped_column(
        String(30), nullable=True, comment="Reuse, Export, Not Applicable"
    )
    source_dataset: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Provenance: fnauman/fashion-second-hand"
    )
    image_urls: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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
    translations: Mapped[list["ProductTranslation"]] = relationship(
        "ProductTranslation", back_populates="product", cascade="all, delete-orphan"
    )
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="products"
    )


class ProductTranslation(TranslationBase):
    """Localised product content — composite PK (product_id, language_code)."""

    __tablename__ = "product_translations"
    __table_args__ = (
        UniqueConstraint("product_id", "language_code", name="uq_product_lang"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    language_code: Mapped[str] = mapped_column(
        String(5), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(
        String(2000), nullable=True
    )

    product: Mapped["Product"] = relationship(
        "Product", back_populates="translations"
    )
