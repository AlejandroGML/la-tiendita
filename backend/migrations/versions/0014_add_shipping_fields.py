"""Add shipping_method and shipping_cost to orders table

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-07

Adds ``shipping_method`` (varchar 50, nullable) and ``shipping_cost``
(numeric 10-2, nullable) columns to the ``orders`` table.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: Union[str, Sequence[str], None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("shipping_method", sa.String(50), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "shipping_cost")
    op.drop_column("orders", "shipping_method")
