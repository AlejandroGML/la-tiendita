"""guest orders — nullable user_id + guest_email

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-13

Allows orders without an authenticated user.  user_id becomes nullable
and a new guest_email column captures the optional contact email for
guest checkout.  Authenticated orders keep user_id set and guest_email
stays NULL.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, Sequence[str], None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Allow orders without a registered user.
    op.alter_column("orders", "user_id", nullable=True)

    # 2. Optional contact email for guest checkouts.
    op.add_column(
        "orders",
        sa.Column("guest_email", sa.VARCHAR(255), nullable=True),
    )


def downgrade() -> None:
    # 2. Drop guest_email column.
    op.drop_column("orders", "guest_email")

    # 1. Restore NOT NULL on user_id.
    # NOTE: will fail if guest orders (user_id=NULL) exist.
    # Delete guest orders or set a placeholder user_id before downgrading.
    op.alter_column("orders", "user_id", nullable=False)
