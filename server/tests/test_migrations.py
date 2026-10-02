import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.models.entities import Eco


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "0002_preserve_eco_history_id.py"
)
SPEC = importlib.util.spec_from_file_location(
    "preserve_eco_history_id",
    MIGRATION_PATH,
)
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)

TEXT_MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "0003_remove_eco_text_limits.py"
)
TEXT_SPEC = importlib.util.spec_from_file_location(
    "remove_eco_text_limits",
    TEXT_MIGRATION_PATH,
)
TEXT_MIGRATION = importlib.util.module_from_spec(
    TEXT_SPEC
)
TEXT_SPEC.loader.exec_module(TEXT_MIGRATION)


@pytest.mark.parametrize(
    ("foreign_keys", "expected_drops"),
    [
        ([], []),
        (
            [
                {
                    "name": "eco_history_eco_id_fkey",
                    "constrained_columns": ["eco_id"],
                }
            ],
            [
                (
                    ("eco_history_eco_id_fkey", "eco_history"),
                    {"type_": "foreignkey"},
                )
            ],
        ),
    ],
)
def test_upgrade_only_drops_existing_eco_id_foreign_key(
    monkeypatch,
    foreign_keys,
    expected_drops,
):
    calls = []
    monkeypatch.setattr(MIGRATION.op, "get_bind", lambda: object())
    monkeypatch.setattr(
        MIGRATION.sa,
        "inspect",
        lambda bind: SimpleNamespace(
            get_foreign_keys=lambda table: foreign_keys
        ),
    )
    monkeypatch.setattr(
        MIGRATION.op,
        "drop_constraint",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    MIGRATION.upgrade()

    assert calls == expected_drops


@pytest.mark.parametrize("foreign_keys", [[], [{
    "name": "eco_history_eco_id_fkey",
    "constrained_columns": ["eco_id"],
    "referred_table": "ecos",
}]])
def test_downgrade_does_not_duplicate_existing_foreign_key(
    monkeypatch,
    foreign_keys,
):
    created = []
    executed = []
    monkeypatch.setattr(MIGRATION.op, "get_bind", lambda: object())
    monkeypatch.setattr(
        MIGRATION.sa,
        "inspect",
        lambda bind: SimpleNamespace(
            get_foreign_keys=lambda table: foreign_keys
        ),
    )
    monkeypatch.setattr(
        MIGRATION.op,
        "execute",
        lambda statement: executed.append(statement),
    )
    monkeypatch.setattr(
        MIGRATION.op,
        "create_foreign_key",
        lambda *args, **kwargs: created.append(args),
    )

    MIGRATION.downgrade()

    assert len(executed) == 1
    assert len(created) == (0 if foreign_keys else 1)


def test_eco_free_text_migration_alters_all_bounded_fields(monkeypatch):
    calls = []
    monkeypatch.setattr(
        TEXT_MIGRATION.op,
        "alter_column",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    TEXT_MIGRATION.upgrade()

    assert len(calls) == len(TEXT_MIGRATION.FIELDS)
    assert "obu" in TEXT_MIGRATION.FIELDS
    assert isinstance(
        Eco.__table__.c.obu.type,
        TEXT_MIGRATION.sa.Text,
    )
    assert all(
        args[0] == "ecos"
        and kwargs["type_"].__class__ is TEXT_MIGRATION.sa.Text
        for args, kwargs in calls
    )

    calls.clear()
    TEXT_MIGRATION.downgrade()

    assert len(calls) == len(TEXT_MIGRATION.FIELDS)
    assert all(
        args[0] == "ecos"
        and kwargs["type_"].__class__ is TEXT_MIGRATION.sa.String
        for args, kwargs in calls
    )