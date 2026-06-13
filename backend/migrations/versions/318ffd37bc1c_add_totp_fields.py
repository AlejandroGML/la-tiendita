"""add totp fields to users

Revision ID: 318ffd37bc1c
Revises: 0006
Create Date: 2026-06-08 20:42:25.132553
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '318ffd37bc1c'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('totp_secret', sa.String(32), nullable=True))
    op.add_column('users', sa.Column('totp_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret')
