"""add product_variants table; seed defaults from products; alter cart_items

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-12

Product variants introduce size×color×stock×SKU as a child table.
Existing products get one default variant each.  Cart identity
switches to partial unique indexes (variant-aware).  Products lose
their legacy size and stock columns.

This migration is fully reversible: the downgrade reconstructs
size/stock from the first variant and reinstates the old cart
constraint.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create product_variants table
    # ------------------------------------------------------------------
    op.create_table(
        "product_variants",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "product_id",
            sa.UUID(),
            sa.ForeignKey("products.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "size",
            sa.Enum(
                "XS", "S", "M", "L", "XL", "XXL",
                name="productsize",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("color", sa.String(100), nullable=True),
        sa.Column(
            "color_hex",
            sa.String(7),
            nullable=True,
            comment="CSS hex e.g. #FF5733",
        ),
        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("sku", sa.String(50), nullable=False, unique=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # 2. Seed one default variant per existing product
    #    SKU: {slug_prefix}-{size|NS}-NC-{seq}
    #    ROW_NUMBER() prevents collisions when slug prefix + size repeats.
    # ------------------------------------------------------------------
    op.execute(
        sa.text(
            """
            INSERT INTO product_variants
                (id, product_id, size, stock, sku, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                p.id,
                p.size,
                COALESCE(p.stock, 1),
                UPPER(LEFT(p.slug, 3))
                    || '-'
                    || COALESCE(p.size::text, 'NS')
                    || '-NC-'
                    || LPAD(
                        ROW_NUMBER() OVER (
                            PARTITION BY UPPER(LEFT(p.slug, 3)),
                                         COALESCE(p.size::text, 'NS')
                            ORDER BY p.slug
                        )::text,
                        2, '0'
                    ),
                p.created_at,
                p.updated_at
            FROM products p
            """
        )
    )

    # ------------------------------------------------------------------
    # 3. Add variant-aware columns to cart_items
    # ------------------------------------------------------------------
    op.add_column(
        "cart_items",
        sa.Column(
            "variant_id",
            sa.UUID(),
            sa.ForeignKey("product_variants.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "cart_items",
        sa.Column("size", sa.String(10), nullable=True),
    )
    op.add_column(
        "cart_items",
        sa.Column("color", sa.String(100), nullable=True),
    )

    # ------------------------------------------------------------------
    # 4. Replace old UniqueConstraint with two partial unique indexes
    # ------------------------------------------------------------------
    op.drop_constraint("uq_cart_user_product", "cart_items", type_="unique")

    op.create_index(
        "uq_cart_user_product",
        "cart_items",
        ["user_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NULL"),
    )
    op.create_index(
        "uq_cart_user_variant",
        "cart_items",
        ["user_id", "variant_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NOT NULL"),
    )

    # ------------------------------------------------------------------
    # 5. Drop legacy size and stock columns from products
    # ------------------------------------------------------------------
    op.drop_column("products", "stock")
    op.drop_column("products", "size")


def downgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Restore size and stock columns on products
    # ------------------------------------------------------------------
    op.add_column(
        "products",
        sa.Column(
            "size",
            sa.Enum(
                "XS", "S", "M", "L", "XL", "XXL",
                name="productsize",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    # ------------------------------------------------------------------
    # 2. Repopulate size/stock from the first variant of each product
    # ------------------------------------------------------------------
    op.execute(
        sa.text(
            """
            UPDATE products p
            SET size  = pv.size,
                stock = COALESCE(pv.stock, 1)
            FROM product_variants pv
            WHERE p.id = pv.product_id
              AND pv.id = (
                  SELECT id FROM product_variants
                  WHERE product_id = p.id
                  ORDER BY created_at
                  LIMIT 1
              )
            """
        )
    )

    # ------------------------------------------------------------------
    # 3. Drop partial unique indexes from cart_items
    # ------------------------------------------------------------------
    op.drop_index(
        "uq_cart_user_product",
        table_name="cart_items",
        postgresql_where=sa.text("variant_id IS NULL"),
    )
    op.drop_index(
        "uq_cart_user_variant",
        table_name="cart_items",
        postgresql_where=sa.text("variant_id IS NOT NULL"),
    )

    # ------------------------------------------------------------------
    # 4. Restore old UniqueConstraint
    # ------------------------------------------------------------------
    op.create_unique_constraint(
        "uq_cart_user_product", "cart_items", ["user_id", "product_id"]
    )

    # ------------------------------------------------------------------
    # 5. Drop variant columns from cart_items
    # ------------------------------------------------------------------
    op.drop_column("cart_items", "size")
    op.drop_column("cart_items", "color")
    op.drop_column("cart_items", "variant_id")

    # ------------------------------------------------------------------
    # 6. Drop product_variants table
    # ------------------------------------------------------------------
    op.drop_table("product_variants")
