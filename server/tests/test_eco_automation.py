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
        eco = Eco(eco="ECO123", obu="OLD", au="OLD-AU", title="Original", change_reason="Reason")
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


def test_missing_and_partial_code(context):
    client, db, eco, _ = context
    for code in ["MISSING", "ECO12", "eco123"]:
        assert client.post(PATH, json={"eco": code, "title": "New"}).status_code == 404
    assert len(db.scalars(select(Eco)).all()) == 1
    assert histories(db) == []


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
    db.add(FieldPermission(user_email=user.email, field_key="title", can_edit=True, can_view=True))
    db.commit()
    assert client.post(PATH, json={"eco": "ECO123", "title": "New", "obu": "NEW"}).status_code == 403
    assert eco.title == "Original" and histories(db) == []
    assert client.post(PATH, json={"eco": "ECO123", "title": "New"}).status_code == 200
    assert eco.title == "New"


@pytest.mark.parametrize("payload", [
    {}, {"eco": "   "}, {"eco": "ECO123", "az_eco_register_date": "2026-02-30"},
    *[{"eco": "ECO123", key: "unexpected"} for key in ["au", "gap_14d", "effective_date", "approved_date", "origin_eco", "suffix", "applied_to_manaus", "prod_plan", "item", "position", "month"]],
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
