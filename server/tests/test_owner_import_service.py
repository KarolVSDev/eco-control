from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config.database import get_db
from app.models.entities import OwnerGroupMapping
from app.services.owner_import_service import OwnerImportService
from app.utils.security import current_user
from main import app


def make_xlsx(*rows, header=("OWNER", "GROUP")):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(header)
    for row in rows:
        worksheet.append(row)

    content = BytesIO()
    workbook.save(content)
    workbook.close()
    return content.getvalue()


@pytest.fixture
def owner_import_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    OwnerGroupMapping.__table__.create(engine)

    with Session(engine) as db:
        yield db

    engine.dispose()


@pytest.fixture
def owner_import_client(owner_import_db):
    overrides_before = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: owner_import_db
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(
        role="admin",
        email="admin@example.com",
    )

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides = overrides_before


def stored_owner_groups(db):
    return db.scalars(select(OwnerGroupMapping)).all()


def test_imports_valid_new_owner_and_normalizes_owner_and_group(owner_import_db):
    content = make_xlsx(("  Ana   Silva  ", "mec"))
    service = OwnerImportService(owner_import_db)

    preview = service.preview_file(content, "owners.xlsx")
    result = service.import_file(content, "owners.xlsx")

    assert preview["can_import"] is True
    assert preview["rows"][0]["owner"] == "Ana Silva"
    assert preview["rows"][0]["group"] == "MEC"
    assert result == {"imported_rows": 1, "duplicate_rows": 0}

    owners = stored_owner_groups(owner_import_db)
    assert [(item.owner, item.group_name) for item in owners] == [
        ("Ana Silva", "MEC"),
    ]


@pytest.mark.parametrize(
    ("row", "expected_message"),
    [
        (("   ", "MEC"), "Owner vazio."),
        (("Ana Silva", "  "), "Group vazio."),
        (("Ana Silva", "XYZ"), "Group inválido."),
    ],
)
def test_empty_fields_and_invalid_group_are_errors(
    owner_import_db,
    row,
    expected_message,
):
    preview = OwnerImportService(owner_import_db).preview_file(
        make_xlsx(row),
        "owners.xlsx",
    )

    assert preview["error_rows"] == 1
    assert preview["can_import"] is False
    assert preview["rows"][0]["status"] == "ERRO"
    assert expected_message in preview["rows"][0]["message"]


def test_repeated_owner_with_same_group_is_duplicate(owner_import_db):
    preview = OwnerImportService(owner_import_db).preview_file(
        make_xlsx(
            ("Ana Silva", "MEC"),
            (" ana   silva ", "mec"),
        ),
        "owners.xlsx",
    )

    assert preview["new_rows"] == 1
    assert preview["duplicate_rows"] == 1
    assert [row["status"] for row in preview["rows"]] == [
        "NOVO",
        "DUPLICADO",
    ]


def test_repeated_owner_with_different_groups_blocks_import(owner_import_db):
    content = make_xlsx(
        ("Ana Silva", "MEC"),
        (" ana   silva ", "DEV"),
    )
    service = OwnerImportService(owner_import_db)
    preview = service.preview_file(content, "owners.xlsx")

    assert preview["conflict_rows"] == 2
    assert preview["can_import"] is False
    assert all(row["status"] == "CONFLITO" for row in preview["rows"])

    with pytest.raises(HTTPException) as error:
        service.import_file(content, "owners.xlsx")

    assert error.value.status_code == 422
    assert stored_owner_groups(owner_import_db) == []


def test_owner_already_in_database_with_same_group_is_duplicate(owner_import_db):
    owner_import_db.add(
        OwnerGroupMapping(owner="João Silva", group_name="MEC")
    )
    owner_import_db.commit()

    service = OwnerImportService(owner_import_db)
    preview = service.preview_file(
        make_xlsx((" joão   silva ", "mec")),
        "owners.xlsx",
    )
    result = service.import_file(
        make_xlsx((" joão   silva ", "mec")),
        "owners.xlsx",
    )

    assert preview["duplicate_rows"] == 1
    assert preview["new_rows"] == 0
    assert preview["can_import"] is False
    assert result == {"imported_rows": 0, "duplicate_rows": 1}
    assert len(stored_owner_groups(owner_import_db)) == 1


def test_owner_already_in_database_with_different_group_is_conflict(owner_import_db):
    owner_import_db.add(
        OwnerGroupMapping(owner="Ana Silva", group_name="MEC")
    )
    owner_import_db.commit()
    content = make_xlsx(("ana   silva", "DEV"))
    service = OwnerImportService(owner_import_db)

    preview = service.preview_file(content, "owners.xlsx")
    assert preview["conflict_rows"] == 1
    assert preview["rows"][0]["status"] == "CONFLITO"

    with pytest.raises(HTTPException) as error:
        service.import_file(content, "owners.xlsx")

    assert error.value.status_code == 422
    owners = stored_owner_groups(owner_import_db)
    assert [(item.owner, item.group_name) for item in owners] == [
        ("Ana Silva", "MEC"),
    ]


def test_new_rows_import_while_simple_duplicates_are_ignored(owner_import_db):
    owner_import_db.add(
        OwnerGroupMapping(owner="Maria Souza", group_name="DEV")
    )
    owner_import_db.commit()
    content = make_xlsx(
        ("Carlos Santos", "BOM"),
        (" maria   souza ", "dev"),
    )

    preview = OwnerImportService(owner_import_db).preview_file(
        content,
        "owners.xlsx",
    )
    result = OwnerImportService(owner_import_db).import_file(
        content,
        "owners.xlsx",
    )

    assert preview["new_rows"] == 1
    assert preview["duplicate_rows"] == 1
    assert result == {"imported_rows": 1, "duplicate_rows": 1}
    assert {
        (item.owner, item.group_name)
        for item in stored_owner_groups(owner_import_db)
    } == {
        ("Maria Souza", "DEV"),
        ("Carlos Santos", "BOM"),
    }


def test_error_prevents_partial_import_of_valid_rows(owner_import_db):
    content = make_xlsx(
        ("Carlos Santos", "BOM"),
        ("Pedro Lima", "XYZ"),
    )

    with pytest.raises(HTTPException) as error:
        OwnerImportService(owner_import_db).import_file(
            content,
            "owners.xlsx",
        )

    assert error.value.status_code == 422
    assert stored_owner_groups(owner_import_db) == []


def test_preview_and_import_endpoints_process_xlsx(owner_import_client):
    content = make_xlsx(("Carlos Santos", "bom"))
    upload = {
        "file": (
            "owners.xlsx",
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    preview = owner_import_client.post(
        "/api/v1/settings/owner-group/import/preview",
        files=upload,
    )
    imported = owner_import_client.post(
        "/api/v1/settings/owner-group/import",
        files=upload,
    )

    assert preview.status_code == 200
    assert preview.json()["new_rows"] == 1
    assert preview.json()["rows"][0]["status"] == "NOVO"
    assert imported.status_code == 200
    assert imported.json() == {"imported_rows": 1, "duplicate_rows": 0}


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/settings/owner-group/import/preview",
        "/api/v1/settings/owner-group/import",
    ],
)
def test_non_admin_cannot_import_owner_groups(owner_import_db, path):
    overrides_before = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: owner_import_db
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(
        role="analyst",
        email="analyst@example.com",
    )

    try:
        response = TestClient(app).post(
            path,
            files={
                "file": (
                    "owners.xlsx",
                    make_xlsx(("Ana Silva", "MEC")),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    finally:
        app.dependency_overrides = overrides_before

    assert response.status_code == 403
    assert stored_owner_groups(owner_import_db) == []
