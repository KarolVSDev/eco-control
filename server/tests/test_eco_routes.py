import pytest
from fastapi.testclient import TestClient

from app.config.database import get_db
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