import importlib.util
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import sqlalchemy as sa
from pydantic import ValidationError
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.models.entities import Eco
from app.schemas.eco import EcoCreate, EcoOut, EcoUpdate
from app.services.eco_service import EcoService


@pytest.mark.parametrize("schema", [EcoCreate, EcoUpdate])
@pytest.mark.parametrize("field,value", [("gap_14d", 15), ("requires_gap_14d_note", True)])
def test_calculated_gap_fields_cannot_be_submitted(schema, field, value):
    with pytest.raises(ValidationError):
        schema(**{field: value})
    assert field not in Eco.__table__.c


@pytest.mark.parametrize("effective,expected,requires", [
    (date(2026, 2, 1), 15, True), (None, None, False),
])
def test_serialized_eco_exposes_gap_fields(effective, expected, requires):
    eco = Eco(
        id=uuid4(), status="RELEASED", effective_date=effective,
        second_aprov_rd_finish_1=date(2026, 2, 16),
    )
    service = EcoService(None, SimpleNamespace(role="admin"))
    data = service.serialize(eco)
    assert data["gap_14d"] == expected
    assert data["requires_gap_14d_note"] is requires
    assert data["computed"]["gap_14d"] == expected
    assert data["computed"]["requires_gap_14d_note"] is requires
    output = EcoOut.model_validate(data)
    assert output.gap_14d == expected
    assert output.requires_gap_14d_note is requires


@pytest.mark.parametrize("schema", [EcoCreate, EcoUpdate])
def test_gap_fields_are_accepted(schema):
    payload = schema(
        effective_date="2026-10-26",
        gap_14d_note="Justificativa\n" + "a" * 1000,
    )
    assert payload.effective_date == date(2026, 10, 26)
    assert payload.gap_14d_note == "Justificativa\n" + "a" * 1000
    assert set(payload.model_dump(exclude_unset=True)) == {
        "effective_date", "gap_14d_note",
    }


@pytest.mark.parametrize("schema", [EcoCreate, EcoUpdate, EcoOut])
def test_gap_fields_are_optional_and_nullable(schema):
    required = {"id": str(uuid4())} if schema is EcoOut else {}
    omitted = schema(**required)
    assert omitted.effective_date is None
    assert omitted.gap_14d_note is None
    assert "effective_date" not in omitted.model_dump(exclude_unset=True)
    assert "gap_14d_note" not in omitted.model_dump(exclude_unset=True)
    cleared = schema(**required, effective_date=None, gap_14d_note=None)
    assert cleared.model_dump(exclude_unset=True) == {
        **required, "effective_date": None, "gap_14d_note": None,
    }


def test_gap_fields_persist_and_are_exposed_by_output_schema():
    engine = sa.create_engine("sqlite://")
    Eco.__table__.create(engine)
    eco_id = uuid4()
    with sa.orm.Session(engine) as session:
        eco = Eco(id=eco_id, **EcoCreate().model_dump(exclude_unset=True))
        session.add(eco)
        session.commit()
        session.refresh(eco)
        assert eco.effective_date is None
        assert eco.gap_14d_note is None

        update = EcoUpdate(effective_date="2026-10-26", gap_14d_note="Motivo")
        for key, value in update.model_dump(exclude_unset=True).items():
            setattr(eco, key, value)
        session.commit()
        session.expire_all()
        persisted = session.get(Eco, eco_id)
        output = EcoOut.model_validate({
            **{("group" if column.name == "group_name" else column.name): getattr(persisted, column.name)
               for column in Eco.__table__.columns if column.name != "id"},
            "id": str(eco_id),
        })
        assert output.model_dump(mode="json")["effective_date"] == "2026-10-26"
        assert output.gap_14d_note == "Motivo"
    engine.dispose()


@pytest.mark.parametrize("existing_columns", [
    [], ["effective_date"], ["gap_14d_note"],
    ["effective_date", "gap_14d_note"],
])
def test_gap_migration_preserves_existing_rows_and_reverses(monkeypatch, existing_columns):
    path = Path(__file__).parents[1] / "alembic/versions/0004_add_gap_report_fields.py"
    spec = importlib.util.spec_from_file_location("add_gap_report_fields", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0004"
    assert migration.down_revision == "0003"

    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE ecos (id INTEGER PRIMARY KEY)")
        connection.exec_driver_sql("INSERT INTO ecos (id) VALUES (1)")
        for name in existing_columns:
            column_type = "DATE" if name == "effective_date" else "TEXT"
            connection.exec_driver_sql(f"ALTER TABLE ecos ADD COLUMN {name} {column_type}")
        operations = Operations(MigrationContext.configure(connection))
        added = []
        dropped = []

        def add_column(table, column):
            added.append(column.name)
            operations.add_column(table, column)

        def drop_column(table, name):
            dropped.append(name)
            operations.drop_column(table, name)

        monkeypatch.setattr(migration, "op", SimpleNamespace(
            get_bind=lambda: connection,
            add_column=add_column,
            drop_column=drop_column,
        ))
        migration.upgrade()
        assert added == [name for name in ("effective_date", "gap_14d_note")
                         if name not in existing_columns]
        migration.upgrade()
        assert len(added) == 2 - len(existing_columns)
        columns = {column["name"]: column for column in sa.inspect(connection).get_columns("ecos")}
        for name, expected_type in [("effective_date", sa.Date), ("gap_14d_note", sa.Text)]:
            assert isinstance(columns[name]["type"], expected_type)
            assert columns[name]["nullable"]
            assert isinstance(Eco.__table__.c[name].type, expected_type)
            assert Eco.__table__.c[name].nullable
        assert connection.exec_driver_sql("SELECT * FROM ecos").one() == (1, None, None)
        migration.downgrade()
        assert dropped == ["gap_14d_note", "effective_date"]
        migration.downgrade()
        assert dropped == ["gap_14d_note", "effective_date"]
        assert [column["name"] for column in sa.inspect(connection).get_columns("ecos")] == ["id"]
        assert connection.exec_driver_sql("SELECT id FROM ecos").scalar_one() == 1
    engine.dispose()


@pytest.mark.parametrize("explicit_denial", [False, True])
def test_all_users_can_edit_and_view_gap_fields(explicit_denial):
    engine = sa.create_engine("sqlite://")
    Eco.__table__.create(engine)
    from app.models.entities import EcoHistory
    EcoHistory.__table__.create(engine)
    with sa.orm.Session(engine) as session:
        eco = Eco(id=uuid4(), status="RELEASED", second_aprov_rd_finish_1=date(2026, 2, 16))
        session.add(eco)
        session.commit()
        service = EcoService(session, SimpleNamespace(
            role="analyst", email="analyst@example.com", full_name="Analyst",
        ))
        permissions = {
            key: SimpleNamespace(can_view=False, can_edit=False)
            for key in ("effective_date", "gap_14d", "gap_14d_note")
        } if explicit_denial else {}
        service._field_permissions = lambda: permissions
        first = service.update(eco.id, EcoUpdate(
            effective_date=date(2026, 2, 1), gap_14d_note="Reason\nLong note",
        ))
        assert first["gap_14d"] == 15
        assert first["requires_gap_14d_note"] is True
        assert first["gap_14d_note"] == "Reason\nLong note"
        second = service.update(eco.id, EcoUpdate(effective_date=date(2026, 2, 5)))
        assert second["gap_14d"] == 11
        assert second["requires_gap_14d_note"] is False
        session.expire_all()
        reloaded = service.serialize(session.get(Eco, eco.id))
        assert reloaded["effective_date"] == date(2026, 2, 5)
        assert reloaded["gap_14d"] == 11
        assert reloaded["gap_14d_note"] == "Reason\nLong note"
        cleared = service.update(eco.id, EcoUpdate(effective_date=None, gap_14d_note=None))
        assert cleared["effective_date"] is None
        assert cleared["gap_14d_note"] is None
        assert cleared["gap_14d"] is None
    engine.dispose()
