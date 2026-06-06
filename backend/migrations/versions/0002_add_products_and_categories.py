"""add products and categories

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create categories, products, and their translation tables."""
    product_condition_enum = sa.Enum(
        "new", "like_new", "good", "fair", name="productcondition"
    )
    product_size_enum = sa.Enum(
        "XS", "S", "M", "L", "XL", "XXL", name="productsize"
    )

    product_condition_enum.create(op.get_bind(), checkfirst=True)
    product_size_enum.create(op.get_bind(), checkfirst=True)

    # --- categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=True)

    # --- categories -> translations ---
    op.create_table(
        "category_translations",
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("language_code", sa.String(5), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("category_id", "language_code"),
        sa.UniqueConstraint(
            "category_id", "language_code", name="uq_category_lang"
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="CASCADE"
        ),
    )

    # --- products ---
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("size", product_size_enum, nullable=True),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("condition", product_condition_enum, nullable=True),
        sa.Column(
            "image_urls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("slug"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(op.f("ix_products_slug"), "products", ["slug"], unique=True)
    op.create_index(
        op.f("ix_products_deleted_at"), "products", ["deleted_at"], unique=False
    )

    # --- products -> translations ---
    op.create_table(
        "product_translations",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("language_code", sa.String(5), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.PrimaryKeyConstraint("product_id", "language_code"),
        sa.UniqueConstraint(
            "product_id", "language_code", name="uq_product_lang"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    """Drop product and category tables + enum types."""
    op.drop_table("product_translations")
    op.drop_index(op.f("ix_products_deleted_at"), table_name="products")
    op.drop_index(op.f("ix_products_slug"), table_name="products")
    op.drop_table("products")
    op.drop_table("category_translations")
    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_table("categories")

    sa.Enum(name="productsize").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="productcondition").drop(op.get_bind(), checkfirst=True)
