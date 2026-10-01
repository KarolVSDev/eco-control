import pytest
from fastapi.testclient import TestClient

from app.config.database import get_db
from app.services.eco_import_service import EcoImportService
from app.services.eco_service import EcoService
from app.utils.security import current_user
from main import app


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("delete", "/api/v1/ecos/31", {}),
        ("patch", "/api/v1/ecos/31", {"json": {"status": "RELEASED"}}),
    ],
)
def test_eco_routes_reject_item_number_as_uuid(method, path, kwargs):
    overrides_before = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[current_user] = lambda: object()

    try:
        response = getattr(TestClient(app), method)(path, **kwargs)
    finally:
        app.dependency_overrides = overrides_before

    assert response.status_code == 422


def test_import_route_delegates_xlsx_to_service(monkeypatch):
    overrides_before = app.dependency_overrides.copy()
    database = object()
    app.dependency_overrides[get_db] = lambda: database
    app.dependency_overrides[current_user] = lambda: object()
    captured = {}

    def fake_import_file(service, content, filename):
        captured["db"] = service.db
        captured["content"] = content
        captured["filename"] = filename
        return {"imported_rows": 1}

    monkeypatch.setattr(
        EcoImportService,
        "import_file",
        fake_import_file,
    )

    try:
        response = TestClient(app).post(
            "/api/v1/ecos/import",
            files={
                "file": (
                    "controle.xlsx",
                    b"xlsx-content",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    finally:
        app.dependency_overrides = overrides_before

    assert response.status_code == 200
    assert response.json() == {"imported_rows": 1}
    assert captured == {
        "db": database,
        "content": b"xlsx-content",
        "filename": "controle.xlsx",
    }


def test_bulk_delete_route_delegates_to_service(monkeypatch):
    overrides_before = app.dependency_overrides.copy()
    database = object()
    app.dependency_overrides[get_db] = lambda: database
    app.dependency_overrides[current_user] = lambda: object()
    captured = {}

    def fake_delete_all(service):
        captured["db"] = service.db
        return {"deleted_rows": 12}

    monkeypatch.setattr(
        EcoService,
        "delete_all",
        fake_delete_all,
    )

    try:
        response = TestClient(app).delete(
            "/api/v1/ecos/bulk/all"
        )
    finally:
        app.dependency_overrides = overrides_before

    assert response.status_code == 200
    assert response.json() == {"deleted_rows": 12}
    assert captured["db"] is database