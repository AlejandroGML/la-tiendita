"""Promotion and PromotionTranslation ORM models — discount codes with i18n."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, TranslationBase

if TYPE_CHECKING:
    from app.models.product import Product


class Promotion(Base):
    """A discount code managed by admins.

    Optional product scope via nullable product_id.
    Usage tracking via max_uses/current_uses.
    Date-range based active window evaluated in service layer.
    """

    __tablename__ = "promotions"
    __table_args__ = (
        CheckConstraint(
            "discount_percent >= 1 AND discount_percent <= 100",
            name="ck_promotion_discount_range",
        ),
        CheckConstraint(
            "max_uses IS NULL OR max_uses >= 1",
            name="ck_promotion_max_uses_positive",
        ),
    )

    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    discount_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    translations: Mapped[list["PromotionTranslation"]] = relationship(
        "PromotionTranslation",
        back_populates="promotion",
        cascade="all, delete-orphan",
    )
    product: Mapped["Product | None"] = relationship("Product")


class PromotionTranslation(TranslationBase):
    """Localised promotion content — composite PK (promotion_id, language_code).

    Follows the same i18n pattern as ProductTranslation and CategoryTranslation.
    """

    __tablename__ = "promotion_translations"
    __table_args__ = (
        UniqueConstraint(
            "promotion_id", "language_code", name="uq_promotion_lang"
        ),
    )

    promotion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("promotions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    language_code: Mapped[str] = mapped_column(
        String(5), primary_key=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )

    promotion: Mapped["Promotion"] = relationship(
        "Promotion", back_populates="translations"
    )
