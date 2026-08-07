"""Multi-provider payments: rename stripe_session_id + add provider columns

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-07

Changes to ``orders``:
- Rename ``stripe_session_id`` → ``payment_reference`` (provider-agnostic:
  stores Stripe session id, Swish payment token, etc.)
- Add ``payment_provider`` (string, default "stripe") — "stripe" | "swish"
- Add ``payment_details`` (JSONB, nullable) — QR payload, payee alias, etc.

Existing rows are preserved: ``alter_column`` renames in place and
``payment_provider`` defaults to "stripe" for historical orders.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0017"
down_revision: Union[str, Sequence[str], None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Renombrar columna de referencia de pago (provider-agnostic)
    op.alter_column(
        "orders",
        "stripe_session_id",
        new_column_name="payment_reference",
    )
    # Proveedor de pago — histórico queda "stripe"
    op.add_column(
        "orders",
        sa.Column(
            "payment_provider",
            sa.String(20),
            nullable=False,
            server_default="stripe",
        ),
    )
    # Detalles específicos del provider (QR de Swish, payee_alias, ...)
    op.add_column(
        "orders",
        sa.Column("payment_details", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "payment_details")
    op.drop_column("orders", "payment_provider")
    op.alter_column(
        "orders",
        "payment_reference",
        new_column_name="stripe_session_id",
    )
