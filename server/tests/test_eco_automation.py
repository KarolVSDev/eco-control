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


def test_hq_release_date_create_repeat_and_update(context):
    client, db, _, user = context
    payload = dict(eco="AUTO_HQ_DATE_TEST_001", title="Teste HQ Release Date",
                   hq_eco_release_date="2026-10-28")
    created = client.post(PATH, json=payload)
    assert created.status_code == 200
    result = created.json()
    assert result["status"] == "created"
    assert "hq_eco_release_date" in result["changed_fields"]
    eco = db.scalar(select(Eco).where(Eco.eco == payload["eco"]))
    assert result["eco_id"] == str(eco.id)
    assert eco.hq_eco_release_date == date(2026, 10, 28)
    assert eco.second_aprov_rd_finish_1 is None and eco.effective_date is None
    event = next(e for e in histories(db) if e.field_key == "hq_eco_release_date")
    assert (event.old_value, event.new_value, event.action) == (None, "2026-10-28", "created")
    assert event.user_email == user.email
    count = len(histories(db))
    repeated = client.post(PATH, json=payload)
    assert repeated.status_code == 200
    assert repeated.json() == dict(status="unchanged", eco_id=str(eco.id),
                                   eco=eco.eco, changed_fields=[])
    assert len(histories(db)) == count
    assert len(db.scalars(select(Eco).where(Eco.eco == payload["eco"])).all()) == 1
    updated = client.post(PATH, json=dict(eco=eco.eco, hq_eco_release_date="2026-10-29"))
    assert updated.status_code == 200
    assert updated.json() == dict(status="updated", eco_id=str(eco.id),
                                  eco=eco.eco, changed_fields=["hq_eco_release_date"])
    assert eco.hq_eco_release_date == date(2026, 10, 29)
    assert eco.title == payload["title"]
    events = histories(db)
    assert len(events) == count + 1
    event = next(e for e in events if e.action == "updated")
    assert (event.field_key, event.old_value, event.new_value) == (
        "hq_eco_release_date", "2026-10-28", "2026-10-29")


@pytest.mark.parametrize("optional", [{}, *[{"hq_eco_release_date": v} for v in [None, "", "   "]]])
def test_hq_release_date_empty_or_omitted_preserves_data(context, optional):
    client, db, eco, _ = context
    eco.hq_eco_release_date = date(2026, 10, 28)
    db.commit()
    response = client.post(PATH, json={"eco": eco.eco, **optional})
    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"
    assert response.json()["changed_fields"] == []
    assert eco.hq_eco_release_date == date(2026, 10, 28)
    assert histories(db) == []


@pytest.mark.parametrize("field", ["az_eco_register_date", "hq_eco_release_date"])
@pytest.mark.parametrize("value", ["28/10/2026", "2026-02-30"])
def test_automation_dates_preserve_existing_validation(context, field, value):
    client, db, _, _ = context
    assert client.post(PATH, json={"eco": "AUTO_HQ_DATE_TEST_002", field: value}).status_code == 422
    assert db.scalar(select(Eco).where(Eco.eco == "AUTO_HQ_DATE_TEST_002")) is None
    assert histories(db) == []


@pytest.mark.parametrize("create", [False, True])
def test_hq_release_date_requires_field_permission(context, create):
    from app.models.entities import AnalystPermission
    client, db, eco, user = context
    user.role = "analyst"
    db.add(AnalystPermission(user_email=user.email, can_create_eco=True))
    for key in ["eco", "group", "owner", "title"]:
        db.add(FieldPermission(user_email=user.email, field_key=key, can_edit=True))
    permission = FieldPermission(user_email=user.email, field_key="hq_eco_release_date", can_edit=False)
    db.add(permission)
    db.commit()
    code = "NEW-HQ" if create else eco.eco
    payload = dict(eco=code, title="Changed", hq_eco_release_date="2026-10-28")
    assert client.post(PATH, json=payload).status_code == 403
    assert eco.title == "Original" and eco.hq_eco_release_date is None
    assert histories(db) == []
    if create:
        assert db.scalar(select(Eco).where(Eco.eco == code)) is None
    permission.can_edit = True
    db.commit()
    response = client.post(PATH, json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == ("created" if create else "updated")
    assert "hq_eco_release_date" in response.json()["changed_fields"]
    permission.can_edit = False
    db.commit()
    count = len(histories(db))
    assert client.post(PATH, json=payload).status_code == 403
    assert len(histories(db)) == count


def test_full_update_audit_and_idempotence(context):
    client, db, eco, user = context

    # O registro existente possui OBU="OLD".
    # Como ECO + OBU agora identificam o registro,
    # utilizamos o mesmo OBU para testar atualização.
    #
    # O mapeamento também permite validar que
    # OBU="OLD" atualiza AU para "NEW-AU".
    db.add(
        ObuAuMapping(
            obu="OLD",
            au="NEW-AU",
        )
    )
    db.commit()

    payload = dict(
        eco=" ECO123 ",
        obu="OLD",
        change_reason="Changed",
        eco_type="TYPE",
        az_eco_register_date="2026-10-27",
        auto_ecr="YES",
        change_bom="NO",
        title="New title",
    )

    response = client.post(
        PATH,
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "updated"

    # O OBU foi enviado, mas não aparece como alterado
    # porque o registro já possuía OBU="OLD".
    #
    # O AU, por outro lado, muda de OLD-AU para NEW-AU.
    expected_changed_fields = (
        set(payload)
        - {"eco", "obu"}
        | {"au"}
    )

    assert (
        set(response.json()["changed_fields"])
        == expected_changed_fields
    )

    assert eco.eco == "ECO123"
    assert eco.obu == "OLD"
    assert eco.au == "NEW-AU"

    assert (
        eco.az_eco_register_date
        == date(2026, 10, 27)
    )

    assert eco.change_reason == "Changed"
    assert eco.eco_type == "TYPE"
    assert eco.auto_ecr == "YES"
    assert eco.change_bom == "NO"
    assert eco.title == "New title"

    events = histories(db)

    # Campos alterados:
    # change_reason
    # eco_type
    # az_eco_register_date
    # auto_ecr
    # change_bom
    # title
    # au
    assert len(events) == 7

    assert all(
        event.action == "updated"
        and event.user_email == user.email
        and event.created_at
        for event in events
    )

    title_event = next(
        event
        for event in events
        if event.field_key == "title"
    )

    assert (
        title_event.old_value,
        title_event.new_value,
    ) == (
        "Original",
        "New title",
    )

    # ---------------------------------------------------------
    # IDEMPOTÊNCIA
    # ---------------------------------------------------------

    second = client.post(
        PATH,
        json=payload,
    ).json()

    assert second["status"] == "unchanged"
    assert second["changed_fields"] == []

    # Nenhum histórico adicional deve ser criado.
    assert len(histories(db)) == 7


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


def test_origin_eco_maps_to_hz_in_kr_eco_1(context):
    client, db, eco, _ = context

    created = client.post(
        PATH,
        json={
            "eco": "ORIGIN-ECO-NEW",
            "origin_eco": "EKLQ500458",
        },
    )

    assert created.status_code == 200
    assert created.json()["status"] == "created"
    assert "origin_eco" in created.json()["changed_fields"]

    new_eco = db.scalar(
        select(Eco).where(Eco.eco == "ORIGIN-ECO-NEW")
    )

    assert new_eco is not None
    assert new_eco.hz_in_kr_eco_1 == "EKLQ500458"

    assert any(
        event.field_key == "hz_in_kr_eco_1"
        and event.new_value == "EKLQ500458"
        for event in histories(db)
    )

    updated = client.post(
        PATH,
        json={
            "eco": eco.eco,
            "origin_eco": "SKLQ900553",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "updated"
    assert updated.json()["changed_fields"] == ["origin_eco"]

    db.refresh(eco)
    assert eco.hz_in_kr_eco_1 == "SKLQ900553"

    repeated = client.post(
        PATH,
        json={
            "eco": eco.eco,
            "origin_eco": "SKLQ900553",
        },
    )

    assert repeated.status_code == 200
    assert repeated.json()["status"] == "unchanged"
    assert repeated.json()["changed_fields"] == []

    db.refresh(eco)
    assert eco.hz_in_kr_eco_1 == "SKLQ900553"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_origin_eco_empty_preserves_existing_data(context, value):
    client, db, eco, _ = context

    eco.hz_in_kr_eco_1 = "EXISTING-ORIGIN"
    db.commit()

    response = client.post(
        PATH,
        json={
            "eco": eco.eco,
            "origin_eco": value,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"
    assert response.json()["changed_fields"] == []

    db.refresh(eco)
    assert eco.hz_in_kr_eco_1 == "EXISTING-ORIGIN"


@pytest.mark.parametrize("payload", [
    {}, {"eco": "   "}, {"eco": "ECO123", "az_eco_register_date": "2026-02-30"},
    *[{"eco": "ECO123", key: "unexpected"} for key in ["group", "group_name", "owner", "au", "gap_14d", "effective_date", "approved_date", "suffix", "applied_to_manaus", "prod_plan", "item", "position", "month"]],
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

    payload = {
        key: empty
        for key in [
            "obu",
            "change_reason",
            "eco_type",
            "az_eco_register_date",
            "hq_eco_release_date",
            "auto_ecr",
            "change_bom",
            "title",
        ]
    }

    payload["eco"] = " NEW-ECO "

    result = client.post(PATH, json=payload)

    assert result.status_code == 200
    assert result.json()["status"] == "created"
    assert set(result.json()["changed_fields"]) == {"eco"}

    new = db.scalar(
        select(Eco).where(
            Eco.eco == "NEW-ECO"
        )
    )

    for key in payload.keys() - {"eco"}:
        assert getattr(new, key) is None

    for key in [
        "effective_date",
        "agreement_start_1",
        "agreement_finish_1",
        "second_aprov_rd_finish_1",
        "gap_14d_note",
        "set_eco",
    ]:
        assert getattr(new, key) is None

    assert new.group_name is None
    assert new.owner is None
    assert new.status == "WORKING"
    assert new.item == 1
    assert new.position == 1
    assert new.month
    assert new.au is None

    events = histories(db)

    assert {
        (event.field_key, event.action)
        for event in events
    } == {
        ("eco", "created"),
    }

    assert client.post(
        PATH,
        json=payload,
    ).json()["status"] == "unchanged"

    assert len(histories(db)) == 1

def test_create_all_available_fields_and_obu_mapping(context):
    client, db, _, user = context

    db.add(
        ObuAuMapping(
            obu="NEW",
            au="NEW-AU",
        )
    )
    db.commit()

    payload = dict(
        eco="NEW-ECO",
        obu="NEW",
        change_reason="Reason",
        eco_type="TYPE",
        az_eco_register_date="2026-10-27",
        auto_ecr="YES",
        change_bom="NO",
        title="Title",
    )

    result = client.post(
        PATH,
        json=payload,
    )

    assert result.status_code == 200
    assert result.json()["status"] == "created"

    new = db.scalar(
        select(Eco).where(
            Eco.eco == "NEW-ECO"
        )
    )

    assert result.json()["eco_id"] == str(new.id)

    for key, value in payload.items():
        assert getattr(new, key) == (
            date(2026, 10, 27)
            if key == "az_eco_register_date"
            else value
        )

    assert new.au == "NEW-AU"

    # A automação não deve inventar nem sobrescrever
    # GROUP e OWNER.
    assert new.group_name is None
    assert new.owner is None

    events = histories(db)

    assert {
        event.field_key
        for event in events
    } == set(payload)

    assert all(
        event.action == "created"
        and event.user_email == user.email
        for event in events
    )

    assert client.post(
        PATH,
        json=payload,
    ).json()["status"] == "unchanged"

    assert len(histories(db)) == len(events)

    assert len(
        db.scalars(
            select(Eco)
        ).all()
    ) == 2

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


def test_automation_preserves_existing_group_and_owner(context):
    client, db, eco, _ = context

    eco.group_name = "DEV"
    eco.owner = "previous.owner"
    db.commit()

    other = Eco(
        eco="UNTOUCHED",
        group_name="HW",
        owner="other.owner",
    )

    db.add(other)
    db.commit()

    response = client.post(
        PATH,
        json={
            "eco": "ECO123",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"
    assert response.json()["changed_fields"] == []

    assert eco.group_name == "DEV"
    assert eco.owner == "previous.owner"

    assert histories(db) == []

    assert (
        other.group_name,
        other.owner,
    ) == (
        "HW",
        "other.owner",
    )

def test_automation_field_permissions_are_enforced(context):
    client, db, eco, user = context

    user.role = "analyst"

    eco.group_name = "DEV"
    eco.owner = "previous.owner"
    db.commit()

    # Sem permissão de edição de title.
    denied = client.post(
        PATH,
        json={
            "eco": "ECO123",
            "title": "New",
        },
    )

    assert denied.status_code == 403

    assert eco.title == "Original"
    assert eco.group_name == "DEV"
    assert eco.owner == "previous.owner"
    assert histories(db) == []

    # Com permissão apenas para title.
    db.add(
        FieldPermission(
            user_email=user.email,
            field_key="title",
            can_edit=True,
        )
    )
    db.commit()

    allowed = client.post(
        PATH,
        json={
            "eco": "ECO123",
            "title": "New",
        },
    )

    assert allowed.status_code == 200
    assert allowed.json()["status"] == "updated"
    assert allowed.json()["changed_fields"] == ["title"]

    assert eco.title == "New"

    # GROUP e OWNER continuam intactos.
    assert eco.group_name == "DEV"
    assert eco.owner == "previous.owner"

    events = histories(db)

    assert len(events) == 1
    assert events[0].field_key == "title"

def test_normal_create_and_patch_do_not_apply_automation_assignments(context):
    client, db, eco, _ = context
    result = client.post("/api/v1/ecos", json={"eco": "MANUAL", "owner": "manual.owner", "group": "DEV"})
    assert result.status_code == 200
    assert result.json()["owner"] == "manual.owner" and result.json()["group"] == "DEV"
    result = client.patch(f"/api/v1/ecos/{eco.id}", json={"owner": "edited.owner", "group": "HW"})
    assert result.status_code == 200
    assert (eco.owner, eco.group_name) == ("edited.owner", "HW")


def test_existing_eco_group_is_preserved_when_not_sent(context):
    client, db, eco, _ = context

    eco.group_name = "DEV"
    eco.owner = "existing.owner"
    db.commit()

    response = client.post(
        PATH,
        json={
            "eco": "ECO123",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"
    assert response.json()["changed_fields"] == []

    assert eco.group_name == "DEV"
    assert eco.owner == "existing.owner"

    assert histories(db) == []
