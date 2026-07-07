"""Add reserved_stock to product_variants for temporary stock reservation

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-07

Adds ``reserved_stock`` (integer, default 0) to ``product_variants``.
Available stock is computed as ``stock - reserved_stock``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0015"
down_revision: Union[str, Sequence[str], None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_variants",
        sa.Column(
            "reserved_stock",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("product_variants", "reserved_stock")
