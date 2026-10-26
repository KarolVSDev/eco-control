"""Add optional persisted fields for the GAP report."""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ecos")}
    if "effective_date" not in columns:
        op.add_column("ecos", sa.Column("effective_date", sa.Date(), nullable=True))
    if "gap_14d_note" not in columns:
        op.add_column("ecos", sa.Column("gap_14d_note", sa.Text(), nullable=True))


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ecos")}
    if "gap_14d_note" in columns:
        op.drop_column("ecos", "gap_14d_note")
    if "effective_date" in columns:
        op.drop_column("ecos", "effective_date")
