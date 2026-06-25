"""fts-search — add search_vector tsvector column with trigger and GIN index

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-25

Adds a generated ``search_vector`` tsvector column to ``product_translations``,
maintained by a BEFORE INSERT OR UPDATE trigger.  The trigger maps
``language_code`` to a PostgreSQL text-search configuration and concatenates
``name`` and ``description``.  Existing rows are backfilled and a GIN index
is built CONCURRENTLY to avoid locking the table.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: Union[str, Sequence[str], None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION trg_product_translations_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector(
        CASE NEW.language_code
            WHEN 'es' THEN 'spanish'::regconfig
            WHEN 'en' THEN 'english'::regconfig
            WHEN 'sv' THEN 'swedish'::regconfig
            ELSE 'simple'::regconfig
        END,
        COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.description, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_DEF = """
CREATE TRIGGER trg_product_translations_search_vector
    BEFORE INSERT OR UPDATE OF name, description, language_code
    ON product_translations
    FOR EACH ROW
    EXECUTE FUNCTION trg_product_translations_search_vector();
"""


def upgrade() -> None:
    # 1. Add the nullable tsvector column — no default, trigger will populate.
    op.add_column(
        "product_translations",
        sa.Column("search_vector", sa.dialects.postgresql.TSVECTOR, nullable=True),
    )

    # 2. Create the trigger function (language-config aware).
    op.execute(TRIGGER_FUNCTION)

    # 3. Attach the trigger to product_translations.
    op.execute(TRIGGER_DEF)

    # 4. Backfill existing rows so the GIN index has data immediately.
    op.execute(
        sa.text(
            """UPDATE product_translations SET name = name"""
        )
    )

    # 5. GIN index built CONCURRENTLY — zero-downtime on write-light tables.
    op.execute(
        sa.text(
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pt_search_vector
               ON product_translations USING GIN(search_vector)"""
        )
    )


def downgrade() -> None:
    # Reverse order: index, trigger, function, column.

    op.execute(
        sa.text("DROP INDEX CONCURRENTLY IF EXISTS idx_pt_search_vector")
    )

    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_product_translations_search_vector "
            "ON product_translations"
        )
    )

    op.execute(
        sa.text("DROP FUNCTION IF EXISTS trg_product_translations_search_vector()")
    )

    op.drop_column("product_translations", "search_vector")
