"""add reviews, wishlist, promotions and promotion_translations

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reviews, wishlist, promotions, and promotion_translations tables."""
    # --- reviews ---
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5", name="ck_review_rating_range"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
        ),
    )
    op.create_index(
        op.f("ix_reviews_user_id"), "reviews", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_reviews_product_id"), "reviews", ["product_id"], unique=False
    )

    # --- wishlist ---
    op.create_table(
        "wishlist",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", "product_id", name="pk_wishlist"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
        ),
    )
    op.create_index(
        op.f("ix_wishlist_user_id"), "wishlist", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_wishlist_product_id"), "wishlist", ["product_id"], unique=False
    )

    # --- promotions ---
    op.create_table(
        "promotions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("discount_percent", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("current_uses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.CheckConstraint(
            "discount_percent >= 1 AND discount_percent <= 100",
            name="ck_promotion_discount_range",
        ),
        sa.CheckConstraint(
            "max_uses IS NULL OR max_uses >= 1",
            name="ck_promotion_max_uses_positive",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="SET NULL",
        ),
    )
    op.create_index(
        op.f("ix_promotions_code"), "promotions", ["code"], unique=True
    )

    # --- promotion_translations ---
    op.create_table(
        "promotion_translations",
        sa.Column("promotion_id", sa.Uuid(), nullable=False),
        sa.Column("language_code", sa.String(5), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.PrimaryKeyConstraint("promotion_id", "language_code", name="pk_promotion_translations"),
        sa.UniqueConstraint(
            "promotion_id", "language_code", name="uq_promotion_lang"
        ),
        sa.ForeignKeyConstraint(
            ["promotion_id"], ["promotions.id"], ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    """Drop reviews, wishlist, promotion_translations, and promotions tables."""
    op.drop_index(op.f("ix_reviews_user_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_product_id"), table_name="reviews")
    op.drop_table("reviews")

    op.drop_index(op.f("ix_wishlist_user_id"), table_name="wishlist")
    op.drop_index(op.f("ix_wishlist_product_id"), table_name="wishlist")
    op.drop_table("wishlist")

    op.drop_table("promotion_translations")

    op.drop_index(op.f("ix_promotions_code"), table_name="promotions")
    op.drop_table("promotions")
