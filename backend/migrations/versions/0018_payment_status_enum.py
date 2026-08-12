"""Convert orders.payment_status from VARCHAR to paymentstatus enum

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-12

The ``Order`` model declares ``payment_status`` as a SQLAlchemy Enum
(PaymentStatus → ``paymentstatus`` type), but migration 0008 created the
column as plain VARCHAR(50). On a fresh production database the enum type
never exists, so INSERTs fail with ``type "paymentstatus" does not exist``.

This migration creates the enum and converts the column, preserving
existing string values (pending/paid/failed/refunded).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0018"
down_revision: Union[str, Sequence[str], None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PAYMENT_STATUS_VALUES = ["pending", "paid", "failed", "refunded"]


def _paymentstatus_enum() -> sa.Enum:
    return sa.Enum(
        *PAYMENT_STATUS_VALUES,
        name="paymentstatus",
        values_callable=lambda x: [e.value for e in x] if hasattr(x[0], "value") else list(x),
    )


def upgrade() -> None:
    paymentstatus = _paymentstatus_enum()
    paymentstatus.create(op.get_bind(), checkfirst=True)

    # Drop the string default so the cast can happen
    op.execute(
        "ALTER TABLE orders ALTER COLUMN payment_status DROP DEFAULT"
    )
    # Cast VARCHAR -> enum
    op.execute(
        "ALTER TABLE orders ALTER COLUMN payment_status "
        "TYPE paymentstatus USING payment_status::paymentstatus"
    )
    # Restore default as the enum-typed value
    op.execute(
        "ALTER TABLE orders ALTER COLUMN payment_status "
        "SET DEFAULT 'pending'::paymentstatus"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE orders ALTER COLUMN payment_status DROP DEFAULT"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN payment_status "
        "TYPE VARCHAR(50) USING payment_status::varchar"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN payment_status SET DEFAULT 'pending'"
    )
    op.execute("DROP TYPE IF EXISTS paymentstatus")
