"""merge totp and payment heads

Revision ID: 5cfde4e3c191
Revises: 0008, 318ffd37bc1c
Create Date: 2026-06-13 11:48:31.788643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cfde4e3c191'
down_revision: Union[str, Sequence[str], None] = ('0008', '318ffd37bc1c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
