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
from app.models.entities import ObuAuMapping
from app.services.obu_au_import_service import (
    ObuAuImportService,
)
from app.utils.security import current_user
from main import app


def make_xlsx(
    *rows,
    header=("OBU", "AU"),
):
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
def obu_au_import_db():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    ObuAuMapping.__table__.create(
        engine
    )

    with Session(engine) as db:
        yield db

    engine.dispose()


@pytest.fixture
def obu_au_import_client(
    obu_au_import_db,
):
    overrides_before = (
        app.dependency_overrides.copy()
    )

    app.dependency_overrides[
        get_db
    ] = lambda: obu_au_import_db

    app.dependency_overrides[
        current_user
    ] = lambda: SimpleNamespace(
        role="admin",
        email="admin@example.com",
    )

    try:
        yield TestClient(app)

    finally:
        app.dependency_overrides = (
            overrides_before
        )


def stored_mappings(db):
    return db.scalars(
        select(
            ObuAuMapping
        )
    ).all()


def test_imports_new_mapping_and_normalizes(
    obu_au_import_db,
):
    content = make_xlsx(
        (
            " nw1 ",
            "glz",
        )
    )

    service = ObuAuImportService(
        obu_au_import_db
    )

    preview = service.preview_file(
        content,
        "obu-au.xlsx",
    )

    result = service.import_file(
        content,
        "obu-au.xlsx",
    )

    assert preview["can_import"] is True
    assert preview["new_rows"] == 1
    assert preview["rows"][0]["obu"] == "NW1"
    assert preview["rows"][0]["au"] == "GLZ"
    assert (
        preview["rows"][0]["status"]
        == "NOVO"
    )

    assert result == {
        "imported_rows": 1,
        "updated_rows": 0,
        "duplicate_rows": 0,
    }

    mappings = stored_mappings(
        obu_au_import_db
    )

    assert [
        (
            item.obu,
            item.au,
        )
        for item in mappings
    ] == [
        (
            "NW1",
            "GLZ",
        )
    ]


@pytest.mark.parametrize(
    (
        "row",
        "expected_message",
    ),
    [
        (
            ("", "GLZ"),
            "OBU vazio.",
        ),
        (
            ("NW1", ""),
            "AU vazio.",
        ),
        (
            ("XXX", "GLZ"),
            "OBU inválido",
        ),
        (
            ("NW1", "XXX"),
            "AU inválido",
        ),
    ],
)
def test_invalid_rows_are_errors(
    obu_au_import_db,
    row,
    expected_message,
):
    preview = (
        ObuAuImportService(
            obu_au_import_db
        )
        .preview_file(
            make_xlsx(row),
            "obu-au.xlsx",
        )
    )

    assert preview[
        "error_rows"
    ] == 1

    assert (
        preview["can_import"]
        is False
    )

    assert (
        preview["rows"][0]["status"]
        == "ERRO"
    )

    assert (
        expected_message
        in preview["rows"][0][
            "message"
        ]
    )


def test_repeated_same_mapping_is_duplicate(
    obu_au_import_db,
):
    preview = (
        ObuAuImportService(
            obu_au_import_db
        )
        .preview_file(
            make_xlsx(
                (
                    "NW1",
                    "GLZ",
                ),
                (
                    "nw1",
                    "glz",
                ),
            ),
            "obu-au.xlsx",
        )
    )

    assert preview[
        "new_rows"
    ] == 1

    assert preview[
        "duplicate_rows"
    ] == 1

    assert [
        row["status"]
        for row
        in preview["rows"]
    ] == [
        "NOVO",
        "DUPLICADO",
    ]


def test_repeated_obu_with_different_au_is_conflict(
    obu_au_import_db,
):
    content = make_xlsx(
        (
            "NW1",
            "GLZ",
        ),
        (
            "NW1",
            "GMZ",
        ),
    )

    service = ObuAuImportService(
        obu_au_import_db
    )

    preview = service.preview_file(
        content,
        "obu-au.xlsx",
    )

    assert preview[
        "conflict_rows"
    ] == 2

    assert (
        preview["can_import"]
        is False
    )

    assert all(
        row["status"]
        == "CONFLITO"
        for row
        in preview["rows"]
    )

    with pytest.raises(
        HTTPException
    ) as error:

        service.import_file(
            content,
            "obu-au.xlsx",
        )

    assert (
        error.value.status_code
        == 422
    )

    assert (
        stored_mappings(
            obu_au_import_db
        )
        == []
    )


def test_existing_same_mapping_is_duplicate(
    obu_au_import_db,
):
    obu_au_import_db.add(
        ObuAuMapping(
            obu="NW1",
            au="GLZ",
        )
    )

    obu_au_import_db.commit()

    content = make_xlsx(
        (
            "nw1",
            "glz",
        )
    )

    service = ObuAuImportService(
        obu_au_import_db
    )

    preview = service.preview_file(
        content,
        "obu-au.xlsx",
    )

    result = service.import_file(
        content,
        "obu-au.xlsx",
    )

    assert preview[
        "duplicate_rows"
    ] == 1

    assert preview[
        "new_rows"
    ] == 0

    assert preview[
        "update_rows"
    ] == 0

    assert (
        preview["can_import"]
        is False
    )

    assert result == {
        "imported_rows": 0,
        "updated_rows": 0,
        "duplicate_rows": 1,
    }


def test_existing_different_au_is_update(
    obu_au_import_db,
):
    obu_au_import_db.add(
        ObuAuMapping(
            obu="NW1",
            au="GLZ",
        )
    )

    obu_au_import_db.commit()

    content = make_xlsx(
        (
            "NW1",
            "PNZ",
        )
    )

    service = ObuAuImportService(
        obu_au_import_db
    )

    preview = service.preview_file(
        content,
        "obu-au.xlsx",
    )

    assert preview[
        "update_rows"
    ] == 1

    assert (
        preview["rows"][0][
            "status"
        ]
        == "ATUALIZAR"
    )

    assert (
        preview["can_import"]
        is True
    )

    result = service.import_file(
        content,
        "obu-au.xlsx",
    )

    assert result == {
        "imported_rows": 0,
        "updated_rows": 1,
        "duplicate_rows": 0,
    }

    mapping = (
        stored_mappings(
            obu_au_import_db
        )[0]
    )

    assert mapping.obu == "NW1"
    assert mapping.au == "PNZ"


def test_mix_new_update_and_duplicate(
    obu_au_import_db,
):
    obu_au_import_db.add_all(
        [
            ObuAuMapping(
                obu="NW1",
                au="GLZ",
            ),
            ObuAuMapping(
                obu="NW4",
                au="PNZ",
            ),
        ]
    )

    obu_au_import_db.commit()

    content = make_xlsx(
        (
            "NW1",
            "GLZ",
        ),
        (
            "NW4",
            "GLZ",
        ),
        (
            "NW5",
            "PNZ",
        ),
    )

    service = ObuAuImportService(
        obu_au_import_db
    )

    preview = service.preview_file(
        content,
        "obu-au.xlsx",
    )

    assert preview[
        "duplicate_rows"
    ] == 1

    assert preview[
        "update_rows"
    ] == 1

    assert preview[
        "new_rows"
    ] == 1

    result = service.import_file(
        content,
        "obu-au.xlsx",
    )

    assert result == {
        "imported_rows": 1,
        "updated_rows": 1,
        "duplicate_rows": 1,
    }

    mappings = {
        item.obu: item.au
        for item
        in stored_mappings(
            obu_au_import_db
        )
    }

    assert mappings == {
        "NW1": "GLZ",
        "NW4": "GLZ",
        "NW5": "PNZ",
    }


def test_error_prevents_partial_import(
    obu_au_import_db,
):
    content = make_xlsx(
        (
            "NW1",
            "GLZ",
        ),
        (
            "XXX",
            "PNZ",
        ),
    )

    with pytest.raises(
        HTTPException
    ) as error:

        ObuAuImportService(
            obu_au_import_db
        ).import_file(
            content,
            "obu-au.xlsx",
        )

    assert (
        error.value.status_code
        == 422
    )

    assert (
        stored_mappings(
            obu_au_import_db
        )
        == []
    )


def test_preview_and_import_endpoints(
    obu_au_import_client,
):
    content = make_xlsx(
        (
            "NW1",
            "glz",
        )
    )

    upload = {
        "file": (
            "obu-au.xlsx",
            content,
            (
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
        )
    }

    preview = (
        obu_au_import_client.post(
            (
                "/api/v1/settings/"
                "obu-au/import/preview"
            ),
            files=upload,
        )
    )

    imported = (
        obu_au_import_client.post(
            (
                "/api/v1/settings/"
                "obu-au/import"
            ),
            files=upload,
        )
    )

    assert (
        preview.status_code
        == 200
    )

    assert (
        preview.json()[
            "new_rows"
        ]
        == 1
    )

    assert (
        preview.json()[
            "rows"
        ][0]["status"]
        == "NOVO"
    )

    assert (
        imported.status_code
        == 200
    )

    assert imported.json() == {
        "imported_rows": 1,
        "updated_rows": 0,
        "duplicate_rows": 0,
    }


@pytest.mark.parametrize(
    "path",
    [
        (
            "/api/v1/settings/"
            "obu-au/import/preview"
        ),
        (
            "/api/v1/settings/"
            "obu-au/import"
        ),
    ],
)
def test_non_admin_cannot_import(
    obu_au_import_db,
    path,
):
    overrides_before = (
        app.dependency_overrides.copy()
    )

    app.dependency_overrides[
        get_db
    ] = lambda: obu_au_import_db

    app.dependency_overrides[
        current_user
    ] = lambda: SimpleNamespace(
        role="analyst",
        email="analyst@example.com",
    )

    try:
        response = (
            TestClient(app).post(
                path,
                files={
                    "file": (
                        "obu-au.xlsx",
                        make_xlsx(
                            (
                                "NW1",
                                "GLZ",
                            )
                        ),
                        (
                            "application/vnd."
                            "openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                    )
                },
            )
        )

    finally:
        app.dependency_overrides = (
            overrides_before
        )

    assert (
        response.status_code
        == 403
    )

    assert (
        stored_mappings(
            obu_au_import_db
        )
        == []
    )