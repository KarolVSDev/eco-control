"""Remove character limits from imported ECO text fields."""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


FIELDS = {
    "product": 120,
    "obu": 30,
    "owner": 255,
    "item_type": 30,
    "eco_type": 120,
    "change_bom": 10,
    "status": 80,
    "receb": 30,
    "eco": 80,
    "auto_ecr": 10,
    "council_meeting_week": 40,
    "hz_in_kr_eco_1": 100,
    "hz_in_kr_eco_2": 100,
    "hz_in_kr_eco_3": 100,
    "az_eco_no": 100,
    "change_bom_az": 10,
    "second_aprov_rd": 100,
    "model_az": 100,
    "new_model": 10,
    "origem_approval": 30,
    "event": 10,
    "set_eco": 100,
    "set_eco_model": 100,
}


def upgrade():
    for column, length in FIELDS.items():
        op.alter_column(
            "ecos",
            column,
            existing_type=sa.String(length=length),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade():
    for column, length in FIELDS.items():
        op.alter_column(
            "ecos",
            column,
            existing_type=sa.Text(),
            type_=sa.String(length=length),
            existing_nullable=True,
        )