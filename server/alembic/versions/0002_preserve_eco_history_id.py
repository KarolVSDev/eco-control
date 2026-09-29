"""Preserve ECO identifiers in audit history after deletion."""

from alembic import op


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "eco_history_eco_id_fkey",
        "eco_history",
        type_="foreignkey",
    )


def downgrade():
    op.execute(
        """
        UPDATE eco_history
        SET eco_id = NULL
        WHERE eco_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM ecos
              WHERE ecos.id = eco_history.eco_id
          )
        """
    )
    op.create_foreign_key(
        "eco_history_eco_id_fkey",
        "eco_history",
        "ecos",
        ["eco_id"],
        ["id"],
        ondelete="SET NULL",
    )