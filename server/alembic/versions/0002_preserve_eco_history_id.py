"""Preserve ECO identifiers in audit history after deletion."""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    foreign_keys = inspector.get_foreign_keys("eco_history")
    constraint_names = {
        foreign_key.get("name")
        for foreign_key in foreign_keys
        if foreign_key.get("constrained_columns") == ["eco_id"]
    }

    for constraint_name in constraint_names:
        if constraint_name:
            op.drop_constraint(
                constraint_name,
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
    inspector = sa.inspect(op.get_bind())
    foreign_keys = inspector.get_foreign_keys("eco_history")
    has_eco_foreign_key = any(
        foreign_key.get("constrained_columns") == ["eco_id"]
        and foreign_key.get("referred_table") == "ecos"
        for foreign_key in foreign_keys
    )

    if not has_eco_foreign_key:
        op.create_foreign_key(
            "eco_history_eco_id_fkey",
            "eco_history",
            "ecos",
            ["eco_id"],
            ["id"],
            ondelete="SET NULL",
        )