from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.eco_service import EcoService
from app.controller import history_controller
from app.controller.history_controller import list_history


def service_with(user, db):
    service = EcoService.__new__(EcoService)
    service.user = user
    service.db = db
    return service


def test_analyst_cannot_create_without_permission():
    db = SimpleNamespace(scalar=lambda query: None)
    service = service_with(SimpleNamespace(role='analyst', email='analyst@example.com'), db)

    assert service._can_create() is False


def test_analyst_cannot_edit_field_without_can_edit():
    permission = SimpleNamespace(field_key='status', can_edit=False)
    scalars_result = SimpleNamespace(all=lambda: [permission])
    db = SimpleNamespace(scalars=lambda query: scalars_result)
    service = service_with(SimpleNamespace(role='analyst', email='analyst@example.com'), db)

    with pytest.raises(HTTPException) as error:
        service._filter_allowed({'status': 'RELEASED'})

    assert error.value.status_code == 403


def test_admin_can_edit_any_schema_field():
    db = SimpleNamespace()
    service = service_with(SimpleNamespace(role='admin', email='admin@example.com'), db)

    assert service._filter_allowed({'status': 'RELEASED'}) == {'status': 'RELEASED'}


def test_analyst_cannot_delete_eco():
    db = SimpleNamespace()
    service = service_with(SimpleNamespace(role='analyst', email='analyst@example.com'), db)

    with pytest.raises(HTTPException) as error:
        service.delete('eco-id')

    assert error.value.status_code == 403


def test_analyst_without_history_permission_gets_403():
    permission = SimpleNamespace(can_view_history=False)
    db = SimpleNamespace(scalar=lambda query: permission)
    user = SimpleNamespace(role='analyst', email='analyst@example.com')

    with pytest.raises(HTTPException) as error:
        list_history(db=db, user=user)

    assert error.value.status_code == 403


def test_analyst_does_not_receive_hidden_history_fields(monkeypatch):
    history_item = SimpleNamespace(
        field_key='status',
        id='history-id',
        eco_id=None,
    )
    permission = SimpleNamespace(can_view_history=True)
    hidden_field = SimpleNamespace(field_key='status', can_view=False)

    class FakeHistoryRepository:
        def __init__(self, db):
            pass

        def list(self, *args):
            return [history_item], 1

    monkeypatch.setattr(history_controller, 'HistoryRepository', FakeHistoryRepository)
    db = SimpleNamespace(
        scalar=lambda query: permission,
        scalars=lambda query: SimpleNamespace(all=lambda: [hidden_field]),
    )
    user = SimpleNamespace(role='analyst', email='analyst@example.com')

    response = list_history(db=db, user=user)

    assert response['items'] == []
    assert response['total'] == 1