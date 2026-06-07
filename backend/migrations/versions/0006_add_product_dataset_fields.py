"""add product dataset fields (condition_rating, condition_details, material, etc.)

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rich product metadata columns from HuggingFace dataset."""
    op.add_column(
        "products",
        sa.Column("condition_rating", sa.Integer(), nullable=True, comment="1-5 quality rating"),
    )
    op.add_column(
        "products",
        sa.Column("condition_details", JSONB(), nullable=True, comment="Structured defects: {pilling, damage, stains, holes, smell}"),
    )
    op.add_column(
        "products",
        sa.Column("target_gender", sa.String(20), nullable=True, comment="Ladies, Men, Kids, Unisex"),
    )
    op.add_column(
        "products",
        sa.Column("material", sa.String(255), nullable=True, comment="e.g. 95%cotton 5%elastan"),
    )
    op.add_column(
        "products",
        sa.Column("colors", JSONB(), nullable=True, comment="e.g. ['Pink', 'Blue']"),
    )
    op.add_column(
        "products",
        sa.Column("trend", sa.String(50), nullable=True, comment="No trend, Sports, 90s, 80s"),
    )
    op.add_column(
        "products",
        sa.Column("pattern", sa.String(50), nullable=True, comment="Floral print, Striped, Animal print"),
    )
    op.add_column(
        "products",
        sa.Column("season", sa.String(20), nullable=True, comment="All, Winter, Summer, Spring, Autumn"),
    )
    op.add_column(
        "products",
        sa.Column("cut", JSONB(), nullable=True, comment="e.g. ['Collar', 'V-collar', 'Cropped']"),
    )
    op.add_column(
        "products",
        sa.Column("usage", sa.String(30), nullable=True, comment="Reuse, Export, Not Applicable"),
    )
    op.add_column(
        "products",
        sa.Column("source_dataset", sa.String(100), nullable=True, comment="Provenance: fnauman/fashion-second-hand"),
    )


def downgrade() -> None:
    """Remove product dataset fields."""
    columns = [
        "condition_rating",
        "condition_details",
        "target_gender",
        "material",
        "colors",
        "trend",
        "pattern",
        "season",
        "cut",
        "usage",
        "source_dataset",
    ]
    for col in columns:
        op.drop_column("products", col)
