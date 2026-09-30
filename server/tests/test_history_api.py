import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config.database import get_db
from app.controller import history_controller
from app.models.entities import EcoHistory
from app.utils.security import current_user
from main import app


@pytest.fixture
def client_and_state(monkeypatch):
    state = SimpleNamespace(
        user=SimpleNamespace(role="admin", email="admin@example.com"),
        db=SimpleNamespace(),
        listed_filters=None,
        exported_filters=None,
        list_items=[],
        total=0,
    )

    class FakeHistoryRepository:
        def __init__(self, db):
            self.db = db

        def list(self, **kwargs):
            state.listed_filters = kwargs
            return state.list_items, state.total

        def iter_filtered(self, **kwargs):
            state.exported_filters = kwargs
            yield from state.list_items

    monkeypatch.setattr(
        history_controller,
        "HistoryRepository",
        FakeHistoryRepository,
    )
    app.dependency_overrides[get_db] = lambda: state.db
    app.dependency_overrides[current_user] = lambda: state.user
    yield TestClient(app), state
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(current_user, None)


def history_row(action="deleted"):
    return EcoHistory(
        id=uuid.uuid4(),
        eco_id=uuid.uuid4(),
        eco_code="ECO-42",
        item=42,
        field_key="status",
        field_label="STATUS",
        old_value="WORKING",
        new_value="RELEASED",
        user_email="admin@example.com",
        user_name="Admin Test",
        action=action,
        created_at=datetime(2026, 9, 29, tzinfo=timezone.utc),
    )


def test_history_list_passes_filters_and_paginates(client_and_state):
    client, state = client_and_state
    state.list_items = [history_row()]
    state.total = 57

    response = client.get(
        "/api/v1/history",
        params={
            "page": 2,
            "page_size": 10,
            "date_start": "2026-09-01T00:00:00",
            "date_end": "2026-09-30T23:59:59",
            "user_email": "admin",
            "field": "status",
            "action": "deleted",
            "eco": "ECO-4",
            "search": "WORKING",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 57
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 10
    assert state.listed_filters["page"] == 2
    assert state.listed_filters["page_size"] == 10
    assert state.listed_filters["action"] == "deleted"
    assert state.listed_filters["search"] == "WORKING"
    assert state.listed_filters["hidden_fields"] == set()


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 501}])
def test_history_rejects_invalid_pagination(client_and_state, params):
    client, _ = client_and_state

    response = client.get("/api/v1/history", params=params)

    assert response.status_code == 422


def test_history_requires_can_view_history(client_and_state):
    client, state = client_and_state
    state.user = SimpleNamespace(role="analyst", email="analyst@example.com")
    state.db.scalar = lambda query: SimpleNamespace(can_view_history=False)

    response = client.get("/api/v1/history")

    assert response.status_code == 403


def test_history_rejects_reversed_date_range(client_and_state):
    client, _ = client_and_state

    response = client.get(
        "/api/v1/history",
        params={
            "date_start": "2026-09-30T00:00:00",
            "date_end": "2026-09-01T00:00:00",
        },
    )

    assert response.status_code == 422


def test_export_returns_filtered_csv(client_and_state):
    client, state = client_and_state
    state.list_items = [history_row()]

    response = client.get(
        "/api/v1/history/export",
        params={"action": "deleted", "search": "ECO-42"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "ECO-42" in response.text
    assert "deleted" in response.text
    assert state.exported_filters["action"] == "deleted"
    assert state.exported_filters["search"] == "ECO-42"


def test_export_requires_can_view_history(client_and_state):
    client, state = client_and_state
    state.user = SimpleNamespace(role="analyst", email="analyst@example.com")
    state.db.scalar = lambda query: SimpleNamespace(can_view_history=False)

    response = client.get("/api/v1/history/export")

    assert response.status_code == 403


def test_analyst_export_passes_hidden_fields_to_repository(client_and_state):
    client, state = client_and_state
    state.user = SimpleNamespace(role="analyst", email="analyst@example.com")
    state.db.scalar = lambda query: SimpleNamespace(can_view_history=True)
    hidden_permission = SimpleNamespace(
        field_key="comments",
        can_view=False,
    )
    state.db.scalars = lambda query: SimpleNamespace(all=lambda: [hidden_permission])

    response = client.get("/api/v1/history/export")

    assert response.status_code == 200
    assert state.exported_filters["hidden_fields"] == {"comments"}