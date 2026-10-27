from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config.database import get_db
from app.models.base import Base
from app.models.entities import Eco, EcoHistory, FieldPermission, ObuAuMapping
from app.schemas.eco import EcoOut
from app.services.eco_service import EcoService
from app.utils.security import current_user
from main import app

PATH = "/api/v1/integrations/eco-automation"


@pytest.fixture
def context():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = SimpleNamespace(role="admin", email="test@example.com", full_name="Test")
        eco = Eco(eco="ECO123", obu="OLD", au="OLD-AU", title="Original", change_reason="Reason",
                  group_name="BOM", owner="giseli.santos")
        db.add(eco)
        db.commit()
        overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[current_user] = lambda: user
        try:
            yield TestClient(app), db, eco, user
        finally:
            app.dependency_overrides = overrides
    engine.dispose()


def histories(db):
    return db.scalars(select(EcoHistory)).all()


def test_full_update_audit_and_idempotence(context):
    client, db, eco, user = context
    db.add(ObuAuMapping(obu="NEW", au="NEW-AU"))
    db.commit()
    payload = dict(eco=" ECO123 ", obu="NEW", change_reason="Changed", eco_type="TYPE",
                   az_eco_register_date="2026-10-27", auto_ecr="YES", change_bom="NO", title="New title")
    response = client.post(PATH, json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    assert set(response.json()["changed_fields"]) == set(payload) - {"eco"} | {"au"}
    assert eco.eco == "ECO123"
    assert eco.au == "NEW-AU"
    assert eco.az_eco_register_date == date(2026, 10, 27)
    for key in set(payload) - {"eco", "az_eco_register_date"}:
        assert getattr(eco, key) == payload[key]
    events = histories(db)
    assert len(events) == 8
    assert all(e.action == "updated" and e.user_email == user.email and e.created_at for e in events)
    title_event = next(e for e in events if e.field_key == "title")
    assert (title_event.old_value, title_event.new_value) == ("Original", "New title")
    second = client.post(PATH, json=payload).json()
    assert second["status"] == "unchanged" and second["changed_fields"] == []
    assert len(histories(db)) == 8


@pytest.mark.parametrize("value", [None, "", "   "])
def test_empty_values_preserve_data(context, value):
    client, db, eco, _ = context
    response = client.post(PATH, json=dict(eco="ECO123", title=value, obu=value,
        change_reason=value, eco_type=value, az_eco_register_date=value, auto_ecr=value, change_bom=value))
    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"
    assert (eco.title, eco.obu, eco.change_reason) == ("Original", "OLD", "Reason")
    assert histories(db) == []


def test_partial_update_and_omitted_fields(context):
    client, db, eco, _ = context
    assert client.post(PATH, json={"eco": "ECO123", "title": "New"}).status_code == 200
    assert (eco.obu, eco.au, eco.change_reason) == ("OLD", "OLD-AU", "Reason")
    assert [e.field_key for e in histories(db)] == ["title"]
    assert client.post(PATH, json={"eco": "ECO123"}).json()["status"] == "unchanged"


def test_missing_and_partial_code_create_separate_records(context):
    client, db, eco, _ = context
    for code in ["MISSING", "ECO12", "eco123"]:
        response = client.post(PATH, json={"eco": code, "title": "New"})
        assert response.status_code == 200
        assert response.json()["status"] == "created"
        assert response.json()["eco"] == code
    assert len(db.scalars(select(Eco)).all()) == 4
    assert eco.title == "Original"


def test_duplicate_normalized_code_changes_nothing(context):
    client, db, eco, _ = context
    other = Eco(eco=" ECO123 ", title="Other")
    db.add(other)
    db.commit()
    assert client.post(PATH, json={"eco": "ECO123", "title": "New"}).status_code == 409
    assert (eco.title, other.title) == ("Original", "Other")
    assert histories(db) == []


def test_field_permissions_are_atomic(context):
    client, db, eco, user = context
    user.role = "analyst"
    assert client.post(PATH, json={"eco": "ECO123", "title": "New"}).status_code == 403
    for key in ["group", "owner"]:
        db.add(FieldPermission(user_email=user.email, field_key=key, can_edit=True))
    db.add(FieldPermission(user_email=user.email, field_key="title", can_edit=True, can_view=True))
    db.commit()
    assert client.post(PATH, json={"eco": "ECO123", "title": "New", "obu": "NEW"}).status_code == 403
    assert eco.title == "Original" and histories(db) == []
    assert client.post(PATH, json={"eco": "ECO123", "title": "New"}).status_code == 200
    assert eco.title == "New"


@pytest.mark.parametrize("payload", [
    {}, {"eco": "   "}, {"eco": "ECO123", "az_eco_register_date": "2026-02-30"},
    *[{"eco": "ECO123", key: "unexpected"} for key in ["group", "group_name", "owner", "au", "gap_14d", "effective_date", "approved_date", "origin_eco", "suffix", "applied_to_manaus", "prod_plan", "item", "position", "month"]],
    {"eco": "ECO123", "auto_ecr": True}, {"eco": "ECO123", "change_bom": "INVALID"},
])
def test_invalid_payload(context, payload):
    client, db, _, _ = context
    assert client.post(PATH, json=payload).status_code == 422
    assert histories(db) == []


def test_authentication_required(context):
    client, _, _, _ = context
    del app.dependency_overrides[current_user]
    assert client.post(PATH, json={"eco": "ECO123"}).status_code == 403
    assert client.post(PATH, json={"eco": "ECO123"}, headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_title_normal_api_create_patch_and_null(context):
    client, db, eco, user = context
    created = client.post("/api/v1/ecos", json={"eco": "CREATED", "title": "Created title"})
    assert created.status_code == 200
    assert created.json()["title"] == "Created title"
    assert client.patch(f"/api/v1/ecos/{eco.id}", json={"title": "Patched"}).json()["title"] == "Patched"
    assert client.patch(f"/api/v1/ecos/{eco.id}", json={"title": None}).json()["title"] is None
    assert EcoOut.model_validate({"id": str(eco.id)}).title is None
    legacy = Eco(eco="LEGACY")
    db.add(legacy)
    db.commit()
    assert EcoService(db, user).serialize(legacy)["title"] is None
    user.role = "analyst"
    assert client.patch(f"/api/v1/ecos/{eco.id}", json={"title": "Denied"}).status_code == 403
    db.add(FieldPermission(user_email=user.email, field_key="title", can_edit=True, can_view=True))
    db.commit()
    assert client.patch(f"/api/v1/ecos/{eco.id}", json={"title": "Allowed"}).json()["title"] == "Allowed"
    assert any(e.field_key == "title" and e.new_value == "Allowed" for e in histories(db))


def test_commit_failure_rolls_back_changes_and_history(context, monkeypatch):
    _, db, eco, user = context
    def fail():
        raise RuntimeError("commit failed")
    monkeypatch.setattr(db, "commit", fail)
    from app.schemas.eco_automation import EcoAutomationRequest
    with pytest.raises(RuntimeError, match="commit failed"):
        EcoService(db, user).sync_automation(EcoAutomationRequest(eco="ECO123", title="New"))
    assert eco.title == "Original"
    assert histories(db) == []


def test_title_migration_upgrade_and_downgrade_preserve_existing_rows():
    import importlib.util
    from pathlib import Path
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import inspect, text

    path = Path(__file__).parents[1] / "alembic/versions/0005_add_eco_title.py"
    spec = importlib.util.spec_from_file_location("title_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0005" and migration.down_revision == "0004"
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ecos (id INTEGER PRIMARY KEY, eco TEXT)"))
        connection.execute(text("INSERT INTO ecos VALUES (1, 'EXISTING')"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            assert connection.execute(text("SELECT eco, title FROM ecos")).one() == ("EXISTING", None)
            title = next(c for c in inspect(connection).get_columns("ecos") if c["name"] == "title")
            assert title["nullable"]
            migration.downgrade()
            assert connection.execute(text("SELECT eco FROM ecos")).scalar_one() == "EXISTING"
            assert "title" not in {c["name"] for c in inspect(connection).get_columns("ecos")}
    engine.dispose()


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_create_ignores_empty_optional_fields_and_uses_defaults(context, empty):
    client, db, _, _ = context
    payload = {key: empty for key in ["obu", "change_reason", "eco_type",
        "az_eco_register_date", "auto_ecr", "change_bom", "title"]}
    payload["eco"] = " NEW-ECO "
    result = client.post(PATH, json=payload)
    assert result.status_code == 200
    assert result.json()["status"] == "created"
    assert set(result.json()["changed_fields"]) == {"eco", "group", "owner"}
    new = db.scalar(select(Eco).where(Eco.eco == "NEW-ECO"))
    for key in payload.keys() - {"eco"}:
        assert getattr(new, key) is None
    for key in ["effective_date", "agreement_start_1", "agreement_finish_1",
                "second_aprov_rd_finish_1", "gap_14d_note", "set_eco"]:
        assert getattr(new, key) is None
    assert new.group_name == "BOM" and new.owner == "giseli.santos"
    assert new.status == "WORKING"
    assert new.item == 1 and new.position == 1 and new.month
    assert new.au is None
    events = histories(db)
    assert {(e.field_key, e.action) for e in events} == {
        ("eco", "created"), ("group", "created"), ("owner", "created")}
    assert client.post(PATH, json=payload).json()["status"] == "unchanged"
    assert len(histories(db)) == 3


def test_create_all_available_fields_and_obu_mapping(context):
    client, db, _, user = context
    from app.models.entities import OwnerGroupMapping
    db.add(OwnerGroupMapping(owner="giseli.santos", group_name="MEC"))
    db.add(ObuAuMapping(obu="NEW", au="NEW-AU"))
    db.commit()
    payload = dict(eco="NEW-ECO", obu="NEW", change_reason="Reason", eco_type="TYPE",
                   az_eco_register_date="2026-10-27", auto_ecr="YES", change_bom="NO", title="Title")
    result = client.post(PATH, json=payload)
    assert result.status_code == 200 and result.json()["status"] == "created"
    new = db.scalar(select(Eco).where(Eco.eco == "NEW-ECO"))
    assert result.json()["eco_id"] == str(new.id)
    for key, value in payload.items():
        assert getattr(new, key) == (date(2026, 10, 27) if key == "az_eco_register_date" else value)
    assert new.au == "NEW-AU"
    assert (new.group_name, new.owner) == ("BOM", "giseli.santos")
    events = histories(db)
    assert {e.field_key for e in events} == set(payload) | {"group", "owner"}
    assert all(e.action == "created" and e.user_email == user.email for e in events)
    assert client.post(PATH, json=payload).json()["status"] == "unchanged"
    assert len(histories(db)) == len(events)
    assert len(db.scalars(select(Eco)).all()) == 2


def test_create_requires_normal_creation_and_field_permissions(context):
    from app.models.entities import AnalystPermission
    client, db, _, user = context
    user.role = "analyst"
    payload = {"eco": "NEW-ECO", "title": "Title"}
    assert client.post(PATH, json=payload).status_code == 403
    db.add(AnalystPermission(user_email=user.email, can_create_eco=True))
    db.add(FieldPermission(user_email=user.email, field_key="eco", can_edit=True))
    db.commit()
    assert client.post(PATH, json=payload).status_code == 403
    assert db.scalar(select(Eco).where(Eco.eco == "NEW-ECO")) is None
    assert histories(db) == []
    db.add(FieldPermission(user_email=user.email, field_key="title", can_edit=True))
    db.commit()
    for key in ["group", "owner"]:
        db.add(FieldPermission(user_email=user.email, field_key=key, can_edit=True))
    db.commit()
    response = client.post(PATH, json=payload)
    assert response.status_code == 200 and response.json()["status"] == "created"


def test_create_commit_failure_rolls_back_record_and_audit(context, monkeypatch):
    from app.schemas.eco_automation import EcoAutomationRequest
    _, db, _, user = context
    def fail():
        raise RuntimeError("commit failed")
    monkeypatch.setattr(db, "commit", fail)
    with pytest.raises(RuntimeError, match="commit failed"):
        EcoService(db, user).sync_automation(EcoAutomationRequest(eco="NEW-ECO", title="Title"))
    assert db.scalar(select(Eco).where(Eco.eco == "NEW-ECO")) is None
    assert histories(db) == []


def test_automation_assignments_update_audit_and_idempotence(context):
    from app.models.entities import OwnerGroupMapping
    client, db, eco, user = context
    eco.group_name = "DEV"
    eco.owner = "previous.owner"
    # Explicit integration group must take priority over owner mapping.
    db.add(OwnerGroupMapping(owner="giseli.santos", group_name="MEC"))
    db.commit()
    other = Eco(eco="UNTOUCHED", group_name="HW", owner="other.owner")
    db.add(other)
    db.commit()
    response = client.post(PATH, json={"eco": "ECO123"})
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    assert set(response.json()["changed_fields"]) == {"group", "owner"}
    assert "group_name" not in response.text
    assert (eco.group_name, eco.owner) == ("BOM", "giseli.santos")
    events = {e.field_key: e for e in histories(db)}
    assert set(events) == {"group", "owner"}
    assert (events["group"].old_value, events["group"].new_value) == ("DEV", "BOM")
    assert (events["owner"].old_value, events["owner"].new_value) == ("previous.owner", "giseli.santos")
    assert all(e.action == "updated" and e.user_email == user.email for e in events.values())
    assert client.post(PATH, json={"eco": "ECO123"}).json()["status"] == "unchanged"
    assert client.post(PATH, json={"eco": "ECO123"}).json()["changed_fields"] == []
    assert len(histories(db)) == 2
    assert (other.group_name, other.owner) == ("HW", "other.owner")


def test_automation_assignment_permissions_are_not_bypassed(context):
    client, db, eco, user = context
    user.role = "analyst"
    eco.owner = "previous.owner"
    db.add(FieldPermission(user_email=user.email, field_key="title", can_edit=True))
    db.commit()
    assert client.post(PATH, json={"eco": "ECO123", "title": "New"}).status_code == 403
    assert eco.owner == "previous.owner" and eco.title == "Original"
    assert histories(db) == []


def test_normal_create_and_patch_do_not_apply_automation_assignments(context):
    client, db, eco, _ = context
    result = client.post("/api/v1/ecos", json={"eco": "MANUAL", "owner": "manual.owner", "group": "DEV"})
    assert result.status_code == 200
    assert result.json()["owner"] == "manual.owner" and result.json()["group"] == "DEV"
    result = client.patch(f"/api/v1/ecos/{eco.id}", json={"owner": "edited.owner", "group": "HW"})
    assert result.status_code == 200
    assert (eco.owner, eco.group_name) == ("edited.owner", "HW")


def test_existing_eco_group_response_uses_external_name(context):
    client, db, eco, _ = context
    eco.group_name = "DEV"
    db.commit()
    response = client.post(PATH, json={"eco": "ECO123"})
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    assert response.json()["changed_fields"] == ["group"]
    assert "group_name" not in response.text
    assert eco.group_name == "BOM"
    events = histories(db)
    assert len(events) == 1
    assert events[0].field_key == "group"
    assert (events[0].old_value, events[0].new_value, events[0].action) == ("DEV", "BOM", "updated")
    second = client.post(PATH, json={"eco": "ECO123"})
    assert second.json()["status"] == "unchanged"
    assert second.json()["changed_fields"] == []
    assert len(histories(db)) == 1
