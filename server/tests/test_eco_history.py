import uuid
from types import SimpleNamespace

from app.models.entities import Eco, EcoHistory
from app.repository.eco_repository import EcoRepository
from app.services.eco_service import EcoService


class HistoryRecorder:
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(event)


class FakeDatabase:
    def __init__(self, shifted_ecos=()):
        self.shifted_ecos = list(shifted_ecos)
        self.committed = False
        self.flushed = False
        self.executed = False
        self.executed_statements = []

    def scalars(self, query):
        return SimpleNamespace(all=lambda: self.shifted_ecos)

    def commit(self):
        self.committed = True

    def flush(self):
        self.flushed = True

    def execute(self, query):
        self.executed = True
        self.executed_statements.append(str(query.compile()))


def make_service(repo, db=None):
    service = EcoService.__new__(EcoService)
    service.user = SimpleNamespace(
        role="admin",
        email="admin@example.com",
        full_name="Admin Test",
    )
    service.repo = repo
    service.db = db or FakeDatabase()
    service.history = HistoryRecorder()
    service.settings = SimpleNamespace(
        au_for_obu=lambda obu: None,
        group_for_owner=lambda owner: None,
    )
    service.serialize = lambda eco: eco
    return service


def test_create_records_each_submitted_field_without_generated_sequence_fields():
    def create(eco):
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

    eco = service.create(payload)

    events = {event.field_key: event for event in service.history.events}
    assert set(events) == {"eco", "status", "comments"}
    assert events["comments"].old_value is None
    assert events["comments"].new_value == "Initial record"
    assert events["comments"].action == "created"
    assert events["comments"].eco_id == eco.id
    assert events["comments"].eco_code == "ECO-12"
    assert events["comments"].item == 12
    assert events["comments"].user_email == "admin@example.com"
    assert events["comments"].user_name == "Admin Test"
    assert events["comments"].field_label == "COMMENTS"
    assert eco.item == 12
    assert eco.position == 8
    assert service.db.committed


def test_update_records_only_fields_that_really_changed():
    eco = Eco(
        id=uuid.uuid4(),
        eco="ECO-7",
        item=7,
        status="WORKING",
        comments="Before",
    )
    service = make_service(
        SimpleNamespace(get=lambda eco_id: eco)
    )
    payload = SimpleNamespace(
        model_dump=lambda **kwargs: {
            "comments": "After",
            "status": "WORKING",
        }
    )

    service.update(eco.id, payload)

    assert len(service.history.events) == 1
    event = service.history.events[0]
    assert event.field_key == "comments"
    assert event.field_label == "COMMENTS"
    assert event.old_value == "Before"
    assert event.new_value == "After"
    assert event.action == "updated"
    assert event.eco_code == "ECO-7"
    assert service.db.committed


def test_delete_records_populated_fields_and_keeps_eco_id():
    eco = Eco(
        id=uuid.uuid4(),
        eco="ECO-3",
        item=3,
        status="RELEASED",
        comments="Final note",
    )
    service = make_service(
        SimpleNamespace(get=lambda eco_id: eco, delete=lambda item: None)
    )

    service.delete(eco.id)

    events = {event.field_key: event for event in service.history.events}
    assert set(events) >= {"eco", "item", "status", "comments"}
    assert events["comments"].old_value == "Final note"
    assert events["comments"].new_value is None
    assert events["comments"].action == "deleted"
    assert events["comments"].eco_id == eco.id
    assert events["comments"].eco_code == "ECO-3"
    assert events["comments"].item == 3
    assert service.db.committed
    assert service.db.flushed


def test_delete_keeps_item_and_audits_position_renumbering():
    eco = Eco(id=uuid.uuid4(), eco="ECO-3", item=3, position=3)
    shifted = Eco(id=uuid.uuid4(), eco="ECO-4", item=4, position=4)
    db = FakeDatabase(shifted_ecos=[shifted])
    service = make_service(
        SimpleNamespace(get=lambda eco_id: eco, delete=lambda item: None),
        db,
    )

    service.delete(eco.id)

    shifted_position_event = next(
        event
        for event in service.history.events
        if event.eco_id == shifted.id and event.field_key == "position"
    )
    assert shifted_position_event.old_value == "4"
    assert shifted_position_event.new_value == "3"
    assert shifted_position_event.action == "updated"
    assert not any(
        event.eco_id == shifted.id and event.field_key == "item"
        for event in service.history.events
    )
    assert "position" in db.executed_statements[0]
    assert "item" not in db.executed_statements[0]
    assert db.executed


def test_history_eco_id_is_not_foreign_key_to_deleted_eco():
    assert not EcoHistory.__table__.c.eco_id.foreign_keys


def test_next_item_never_reuses_deleted_item_from_history():
    values = iter([31, 40])
    repository = EcoRepository(
        SimpleNamespace(scalar=lambda query: next(values))
    )

    assert repository.next_item() == 41


def test_next_position_uses_current_position_sequence():
    repository = EcoRepository(
        SimpleNamespace(scalar=lambda query: 7)
    )

    assert repository.next_position() == 8