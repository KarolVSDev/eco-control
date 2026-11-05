"""Seed default Owner -> Group mappings."""

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


DEFAULT_OWNER_GROUP = [
    ("adriano.junior", "MEC"),
    ("andre.pastor", "HW"),
    ("arialdo.junior", "DEV"),
    ("chrystian.viana", "MEC"),
    ("euler.nogueira", "MEC"),
    ("felipe.castro", "HW"),
    ("gabriel.duarte", "BOM"),
    ("giseli.santos", "BOM"),
    ("joao.serudo", "DEV"),
    ("jorge.junior", "MEC"),
    ("kamila.pimentel", "BOM"),
    ("leandro.moraes", "MEC"),
    ("lucas.maciel", "HW"),
    ("lucash.silva", "MEC"),
    ("marcio.silveira", "DEV"),
    ("marcosfrei.silva", "HW"),
    ("maria.ribeiro", "HW"),
    ("norberto.dias", "HW"),
    ("pedro.silva", "DEV"),
    ("ragison.oliveira", "HW"),
    ("rodrigobastos.silva", "MEC"),
    ("wallacea.roberto", "DEV"),
    ("washingtond.pereira", "DEV"),
    ("wellington.nogueira", "MEC"),
]


def upgrade():
    table = sa.table(
        "owner_group_mappings",
        sa.column(
            "id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.column(
            "owner",
            sa.String(255),
        ),
        sa.column(
            "group_name",
            sa.String(30),
        ),
    )

    rows = [
        {
            "id": uuid.uuid4(),
            "owner": owner,
            "group_name": group_name,
        }
        for owner, group_name
        in DEFAULT_OWNER_GROUP
    ]

    statement = (
        postgresql
        .insert(table)
        .values(rows)
        .on_conflict_do_nothing(
            index_elements=["owner"]
        )
    )

    op.get_bind().execute(
        statement
    )


def downgrade():
    # Não removemos automaticamente os Owners,
    # pois eles podem ter sido editados pelo
    # administrador após a instalação.
    pass