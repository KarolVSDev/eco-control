import uuid
from types import SimpleNamespace

import pytest

from fastapi import HTTPException

from app.models.entities import Eco, EcoHistory
from app.repository.eco_repository import EcoRepository
from app.services.eco_service import EcoService


# =========================================================
# AUXILIARES DE TESTE
# =========================================================


class HistoryRecorder:

    def __init__(self):
        self.events = []


    def add(
        self,
        event,
    ):
        self.events.append(
            event
        )


class FakeDatabase:

    def __init__(
        self,
        shifted_ecos=(),
    ):
        self.shifted_ecos = list(
            shifted_ecos
        )

        self.committed = False
        self.rolled_back = False
        self.flushed = False
        self.refreshed = False
        self.executed = False

        self.executed_statements = []


    def scalars(
        self,
        query,
    ):
        return SimpleNamespace(
            all=lambda:
                self.shifted_ecos
        )


    def commit(
        self,
    ):
        self.committed = True


    def rollback(
        self,
    ):
        self.rolled_back = True


    def flush(
        self,
    ):
        self.flushed = True


    def refresh(
        self,
        obj,
    ):
        self.refreshed = True


    def execute(
        self,
        query,
    ):
        self.executed = True

        self.executed_statements.append(
            str(
                query.compile()
            )
        )


def make_service(
    repo,
    db=None,
):

    service = EcoService.__new__(
        EcoService
    )

    service.user = SimpleNamespace(
        role="admin",
        email="admin@example.com",
        full_name="Admin Test",
    )

    service.repo = repo

    service.db = (
        db
        or FakeDatabase()
    )

    service.history = (
        HistoryRecorder()
    )

    service.settings = (
        SimpleNamespace(
            au_for_obu=lambda obu: None,
            group_for_owner=lambda owner: None,
        )
    )

    service.serialize = (
        lambda eco: eco
    )

    return service


# =========================================================
# CREATE NORMAL
# =========================================================


def test_create_records_each_submitted_field_without_generated_sequence_fields():

    def create(
        eco,
    ):
        eco.id = uuid.uuid4()

        return eco


    service = make_service(
        SimpleNamespace(
            next_item=lambda: 12,
            next_position=lambda: 8,
            create=create,
        )
    )


    payload = SimpleNamespace(
        model_dump=lambda **kwargs: {
            "eco": "ECO-12",
            "status": "WORKING",
            "comments": "Initial record",
        }
    )


    eco = service.create(
        payload
    )


    events = {
        event.field_key: event
        for event
        in service.history.events
    }


    assert set(events) == {
        "eco",
        "status",
        "comments",
    }


    assert (
        events["comments"].old_value
        is None
    )

    assert (
        events["comments"].new_value
        == "Initial record"
    )

    assert (
        events["comments"].action
        == "created"
    )

    assert (
        events["comments"].eco_id
        == eco.id
    )

    assert (
        events["comments"].eco_code
        == "ECO-12"
    )

    assert (
        events["comments"].item
        == 12
    )

    assert (
        events["comments"].user_email
        == "admin@example.com"
    )

    assert (
        events["comments"].user_name
        == "Admin Test"
    )

    assert (
        events["comments"].field_label
        == "COMMENTS"
    )


    assert eco.item == 12

    assert eco.position == 8

    assert service.db.committed


# =========================================================
# CREATE ABAIXO
# =========================================================


def test_create_after_uses_next_sequential_item_and_shifts_existing_items():

    reference = Eco(
        id=uuid.uuid4(),
        eco="ECO-7",
        item=7,
        position=7,
    )


    shifted = Eco(
        id=uuid.uuid4(),
        eco="ECO-8",
        item=8,
        position=8,
    )


    calls = {
        "shift_items_up_from": [],
        "make_space_at_position": [],
    }


    def shift_items_up_from(
        item,
    ):
        calls[
            "shift_items_up_from"
        ].append(
            item
        )


    def make_space_at_position(
        position,
    ):
        calls[
            "make_space_at_position"
        ].append(
            position
        )


    def create(
        eco,
    ):
        eco.id = uuid.uuid4()

        return eco


    repo = SimpleNamespace(
        get=lambda eco_id: reference,
        shift_items_up_from=(
            shift_items_up_from
        ),
        make_space_at_position=(
            make_space_at_position
        ),
        create=create,
    )


    db = FakeDatabase(
        shifted_ecos=[
            shifted
        ]
    )


    service = make_service(
        repo,
        db,
    )


    created = service.create_after(
        reference.id
    )


    # Nova ECO deve ocupar ITEM 8.
    assert created.item == 8


    # Deve ocupar a posição imediatamente
    # abaixo da ECO selecionada.
    assert created.position == 7


    # Os ITEMs a partir de 8 devem
    # ser deslocados.
    assert (
        calls[
            "shift_items_up_from"
        ]
        == [8]
    )


    # A posição visual também precisa
    # abrir espaço.
    assert (
        calls[
            "make_space_at_position"
        ]
        == [7]
    )


    assert service.db.committed

    assert service.db.refreshed


    # Deve existir histórico informando
    # que o antigo ITEM 8 virou 9.
    shifted_item_event = next(
        event
        for event
        in service.history.events
        if (
            event.eco_id
            == shifted.id
            and event.field_key
            == "item"
        )
    )


    assert (
        shifted_item_event.old_value
        == "8"
    )

    assert (
        shifted_item_event.new_value
        == "9"
    )

    assert (
        shifted_item_event.action
        == "updated"
    )


# =========================================================
# UPDATE
# =========================================================


def test_update_records_only_fields_that_really_changed():

    eco = Eco(
        id=uuid.uuid4(),
        eco="ECO-7",
        item=7,
        status="WORKING",
        comments="Before",
    )


    service = make_service(
        SimpleNamespace(
            get=lambda eco_id: eco
        )
    )


    payload = SimpleNamespace(
        model_dump=lambda **kwargs: {
            "comments": "After",
            "status": "WORKING",
        }
    )


    service.update(
        eco.id,
        payload,
    )


    assert (
        len(
            service.history.events
        )
        == 1
    )


    event = (
        service.history.events[0]
    )


    assert (
        event.field_key
        == "comments"
    )

    assert (
        event.field_label
        == "COMMENTS"
    )

    assert (
        event.old_value
        == "Before"
    )

    assert (
        event.new_value
        == "After"
    )

    assert (
        event.action
        == "updated"
    )

    assert (
        event.eco_code
        == "ECO-7"
    )

    assert service.db.committed


# =========================================================
# DELETE - HISTÓRICO DA ECO EXCLUÍDA
# =========================================================


def test_delete_records_populated_fields_and_keeps_eco_id():

    eco = Eco(
        id=uuid.uuid4(),
        eco="ECO-3",
        item=3,
        status="RELEASED",
        comments="Final note",
    )


    repo = SimpleNamespace(
        get=lambda eco_id: eco,
        delete=lambda item: None,
        shift_items_down_after=(
            lambda deleted_item: None
        ),
        close_space_after_position=(
            lambda deleted_position: None
        ),
    )


    service = make_service(
        repo
    )


    service.delete(
        eco.id
    )


    events = {
        event.field_key: event
        for event
        in service.history.events
    }


    assert set(events) >= {
        "eco",
        "item",
        "status",
        "comments",
    }


    assert (
        events["comments"].old_value
        == "Final note"
    )

    assert (
        events["comments"].new_value
        is None
    )

    assert (
        events["comments"].action
        == "deleted"
    )

    assert (
        events["comments"].eco_id
        == eco.id
    )

    assert (
        events["comments"].eco_code
        == "ECO-3"
    )

    assert (
        events["comments"].item
        == 3
    )


    assert service.db.committed

    assert service.db.flushed


# =========================================================
# DELETE - RENUMERAÇÃO
# =========================================================


def test_delete_renumbers_item_and_position_and_records_history():

    eco = Eco(
        id=uuid.uuid4(),
        eco="ECO-3",
        item=3,
        position=3,
    )


    shifted = Eco(
        id=uuid.uuid4(),
        eco="ECO-4",
        item=4,
        position=4,
    )


    calls = {
        "shift_items_down_after": [],
        "close_space_after_position": [],
    }


    def shift_items_down_after(
        deleted_item,
    ):
        calls[
            "shift_items_down_after"
        ].append(
            deleted_item
        )


    def close_space_after_position(
        deleted_position,
    ):
        calls[
            "close_space_after_position"
        ].append(
            deleted_position
        )


    repo = SimpleNamespace(
        get=lambda eco_id: eco,
        delete=lambda item: None,
        shift_items_down_after=(
            shift_items_down_after
        ),
        close_space_after_position=(
            close_space_after_position
        ),
    )


    db = FakeDatabase(
        shifted_ecos=[
            shifted
        ]
    )


    service = make_service(
        repo,
        db,
    )


    service.delete(
        eco.id
    )


    # -----------------------------------------------------
    # HISTÓRICO DO ITEM
    # -----------------------------------------------------

    shifted_item_event = next(
        event
        for event
        in service.history.events
        if (
            event.eco_id
            == shifted.id
            and event.field_key
            == "item"
        )
    )


    assert (
        shifted_item_event.old_value
        == "4"
    )

    assert (
        shifted_item_event.new_value
        == "3"
    )

    assert (
        shifted_item_event.action
        == "updated"
    )


    # -----------------------------------------------------
    # HISTÓRICO DA POSITION
    # -----------------------------------------------------

    shifted_position_event = next(
        event
        for event
        in service.history.events
        if (
            event.eco_id
            == shifted.id
            and event.field_key
            == "position"
        )
    )


    assert (
        shifted_position_event.old_value
        == "4"
    )

    assert (
        shifted_position_event.new_value
        == "3"
    )

    assert (
        shifted_position_event.action
        == "updated"
    )


    # -----------------------------------------------------
    # REPOSITORY
    # -----------------------------------------------------

    assert (
        calls[
            "shift_items_down_after"
        ]
        == [3]
    )


    assert (
        calls[
            "close_space_after_position"
        ]
        == [3]
    )


    assert db.flushed

    assert db.committed


# =========================================================
# HISTÓRICO
# =========================================================


def test_history_eco_id_is_not_foreign_key_to_deleted_eco():

    assert not (
        EcoHistory
        .__table__
        .c
        .eco_id
        .foreign_keys
    )


# =========================================================
# PRÓXIMO ITEM
# =========================================================


def test_next_item_uses_current_item_sequence():

    repository = EcoRepository(
        SimpleNamespace(
            scalar=lambda query: 31
        )
    )


    assert (
        repository.next_item()
        == 32
    )


# =========================================================
# PRÓXIMA POSITION
# =========================================================


def test_next_position_uses_current_position_sequence():

    repository = EcoRepository(
        SimpleNamespace(
            scalar=lambda query: 7
        )
    )


    assert (
        repository.next_position()
        == 8
    )


def test_delete_all_executes_one_bulk_delete_and_commits():

    statements = []
    commits = []
    rollbacks = []
    database = SimpleNamespace(
        scalar=lambda query: 12,
        execute=statements.append,
        commit=lambda: commits.append(True),
        rollback=lambda: rollbacks.append(True),
    )
    service = make_service(
        repo=None,
        db=database,
    )

    result = service.delete_all()

    assert result == {"deleted_rows": 12}
    assert len(statements) == 1
    assert str(statements[0]).lower() == "delete from ecos"
    assert commits == [True]
    assert rollbacks == []


def test_delete_all_rejects_non_admin():

    service = make_service(
        repo=None,
        db=SimpleNamespace(),
    )
    service.user.role = "analyst"

    with pytest.raises(HTTPException) as error:
        service.delete_all()

    assert error.value.status_code == 403