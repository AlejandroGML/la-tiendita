"""guest cart items — nullable user_id + session_id with XOR scope

Revision ID: 0009
Revises: 5cfde4e3c191
Create Date: 2026-06-13

Makes cart_items dual-scope so both authenticated users (user_id) and
guest sessions (session_id) can own cart rows.  An XOR CHECK constraint
enforces exactly one scope per row.  Partial unique indexes are split
into user-scope and session-scope pairs to preserve per-scope uniqueness:
one row per (scope, product) without variant, one per (scope, variant).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, Sequence[str], None] = "5cfde4e3c191"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Make user_id nullable — existing rows keep their value.
    op.alter_column("cart_items", "user_id", nullable=True)

    # 2. Add session_id column for guest-scoped carts.
    op.add_column(
        "cart_items",
        sa.Column("session_id", sa.UUID(), nullable=True),
    )

    # 3. XOR CHECK: exactly one of (user_id, session_id) must be non-null.
    op.create_check_constraint(
        "ck_cart_xor_scope",
        "cart_items",
        sa.text(
            "((user_id IS NOT NULL AND session_id IS NULL)"
            " OR (user_id IS NULL AND session_id IS NOT NULL))"
        ),
    )

    # 4. Drop the two existing partial unique indexes (created in 0007).
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

    # 5. Create four partial unique indexes — two per scope.
    #    user-scope: unique on (user_id, product_id) when no variant
    op.create_index(
        "uq_cart_user_product",
        "cart_items",
        ["user_id", "product_id"],
        unique=True,
        postgresql_where=sa.text(
            "user_id IS NOT NULL AND variant_id IS NULL"
        ),
    )
    #    user-scope: unique on (user_id, variant_id) when variant present
    op.create_index(
        "uq_cart_user_variant",
        "cart_items",
        ["user_id", "variant_id"],
        unique=True,
        postgresql_where=sa.text(
            "user_id IS NOT NULL AND variant_id IS NOT NULL"
        ),
    )
    #    session-scope: unique on (session_id, product_id) when no variant
    op.create_index(
        "uq_cart_session_product",
        "cart_items",
        ["session_id", "product_id"],
        unique=True,
        postgresql_where=sa.text(
            "session_id IS NOT NULL AND variant_id IS NULL"
        ),
    )
    #    session-scope: unique on (session_id, variant_id) when variant present
    op.create_index(
        "uq_cart_session_variant",
        "cart_items",
        ["session_id", "variant_id"],
        unique=True,
        postgresql_where=sa.text(
            "session_id IS NOT NULL AND variant_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    # Reverse operations in opposite order.

    # 5. Drop the four new partial unique indexes.
    op.drop_index(
        "uq_cart_session_variant",
        table_name="cart_items",
        postgresql_where=sa.text(
            "session_id IS NOT NULL AND variant_id IS NOT NULL"
        ),
    )
    op.drop_index(
        "uq_cart_session_product",
        table_name="cart_items",
        postgresql_where=sa.text(
            "session_id IS NOT NULL AND variant_id IS NULL"
        ),
    )
    op.drop_index(
        "uq_cart_user_variant",
        table_name="cart_items",
        postgresql_where=sa.text(
            "user_id IS NOT NULL AND variant_id IS NOT NULL"
        ),
    )
    op.drop_index(
        "uq_cart_user_product",
        table_name="cart_items",
        postgresql_where=sa.text(
            "user_id IS NOT NULL AND variant_id IS NULL"
        ),
    )

    # 4. Restore the two original partial unique indexes (user-only scope).
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

    # 3. Drop the XOR CHECK constraint.
    op.drop_constraint("ck_cart_xor_scope", "cart_items", type_="check")

    # 2. Drop session_id column.
    op.drop_column("cart_items", "session_id")

    # 1. Restore NOT NULL on user_id.
    # NOTE: this will fail if guest-cart rows (user_id=NULL) exist.
    # That is acceptable for a dev downgrade — truncate guest rows first.
    op.alter_column("cart_items", "user_id", nullable=False)
