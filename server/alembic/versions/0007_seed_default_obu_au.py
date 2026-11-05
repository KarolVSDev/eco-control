"""Seed default OBU -> AU mappings."""

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


DEFAULT_OBU_AU = [
    ("NW1", "GLZ"),
    ("NW4", "PNZ"),
    ("NW5", "PNZ"),
    ("NW9", "GMZ"),
    ("NWD", "GLZ"),
    ("NWE", "GLZ"),
    ("NWH", "GMZ"),
    ("NWK", "LMZ"),
    ("NWU", "PNZ"),
    ("NWV", "PGZ"),
    ("NWW", "GMZ"),
    ("NWX", "PNZ"),
    ("NWZ", "GLZ"),
    ("NYE", "GMZ"),
]


def upgrade():
    table = sa.table(
        "obu_au_mappings",
        sa.column(
            "id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.column(
            "obu",
            sa.String(30),
        ),
        sa.column(
            "au",
            sa.String(30),
        ),
    )

    rows = [
        {
            "id": uuid.uuid4(),
            "obu": obu,
            "au": au,
        }
        for obu, au in DEFAULT_OBU_AU
    ]

    statement = (
        postgresql
        .insert(table)
        .values(rows)
        .on_conflict_do_nothing(
            index_elements=["obu"]
        )
    )

    op.get_bind().execute(
        statement
    )


def downgrade():
    # Não removemos relações no downgrade,
    # pois elas podem ter sido editadas pelo
    # administrador depois da instalação.
    pass