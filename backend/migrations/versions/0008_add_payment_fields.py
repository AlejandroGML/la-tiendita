"""add payment_status and stripe_session_id to orders

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-13

Adds payment lifecycle tracking (pending → paid → refunded, or failed)
and a unique Stripe session reference for webhook idempotency.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "payment_status",
            sa.VARCHAR(length=50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "stripe_session_id",
            sa.VARCHAR(length=255),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_orders_stripe_session_id",
        "orders",
        ["stripe_session_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_orders_stripe_session_id", "orders", type_="unique")
    op.drop_column("orders", "stripe_session_id")
    op.drop_column("orders", "payment_status")
