"""Add nullable ECO title."""

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    columns = {
        column["name"]
        for column in sa.inspect(
            op.get_bind()
        ).get_columns("ecos")
    }

    if "title" not in columns:
        op.add_column(
            "ecos",
            sa.Column(
                "title",
                sa.Text(),
                nullable=True,
            ),
        )


def downgrade():
    columns = {
        column["name"]
        for column in sa.inspect(
            op.get_bind()
        ).get_columns("ecos")
    }

    if "title" in columns:
        op.drop_column(
            "ecos",
            "title",
        )