"""Add GDPR consent columns to users and newsletter_subscribers

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-08

Adds to ``users``:
- marketing_consent (boolean, default false)
- consent_at (timestamptz, nullable)
- terms_accepted_at (timestamptz, nullable)

Adds to ``newsletter_subscribers``:
- consent_ip (string, nullable)
- consent_user_agent (string, nullable)
- unsubscribed_at (timestamptz, nullable)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016"
down_revision: Union[str, Sequence[str], None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.add_column(
        "users",
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # newsletter_subscribers
    op.add_column(
        "newsletter_subscribers",
        sa.Column("consent_ip", sa.String(45), nullable=True),
    )
    op.add_column(
        "newsletter_subscribers",
        sa.Column("consent_user_agent", sa.String(500), nullable=True),
    )
    op.add_column(
        "newsletter_subscribers",
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "marketing_consent")
    op.drop_column("users", "consent_at")
    op.drop_column("users", "terms_accepted_at")
    op.drop_column("newsletter_subscribers", "consent_ip")
    op.drop_column("newsletter_subscribers", "consent_user_agent")
    op.drop_column("newsletter_subscribers", "unsubscribed_at")
