"""Category and CategoryTranslation ORM models — SERIAL PK override."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TranslationBase

if TYPE_CHECKING:
    from app.models.product import Product


class Category(Base):
    """Product category with SERIAL primary key (intentional deviation from UUID)."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    translations: Mapped[list["CategoryTranslation"]] = relationship(
        "CategoryTranslation", back_populates="category", cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="category"
    )


class CategoryTranslation(TranslationBase):
    """Localised category name — composite PK (category_id, language_code)."""

    __tablename__ = "category_translations"
    __table_args__ = (
        UniqueConstraint("category_id", "language_code", name="uq_category_lang"),
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )
    language_code: Mapped[str] = mapped_column(
        String(5), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped["Category"] = relationship(
        "Category", back_populates="translations"
    )
