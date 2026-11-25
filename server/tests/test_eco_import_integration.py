import os
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models.entities import Eco, EcoHistory
from app.services.eco_import_service import EcoImportService
from test_eco_import_service import create_workbook


TEST_ITEM = 900001
TEST_ECO = "ECO-TEST-INTEGRATION-001"


@pytest.fixture
def db_engine():
    raw_url = os.environ.get("DATABASE_URL", "")
    if not raw_url:
        pytest.fail("DATABASE_URL nao configurada.")

    url = make_url(raw_url)

    if not (
        url.database == "eco_control_integration_test"
        and url.host in ("localhost", "127.0.0.1")
        and url.port == 5435
        and url.username == "eco_test_user"
    ):
        pytest.fail("BLOQUEADO: banco de testes incorreto.")

    engine = create_engine(raw_url)

    try:
        with engine.connect() as connection:
            database, username = connection.exec_driver_sql(
                "SELECT current_database(), current_user"
            ).one()

            if (
                database != "eco_control_integration_test"
                or username != "eco_test_user"
            ):
                pytest.fail(
                    "BLOQUEADO: identidade do banco incorreta."
                )

        yield engine
    finally:
        engine.dispose()


def test_reimport_updates_item_and_records_history(db_engine):
    user = SimpleNamespace(
        role="admin",
        email="integration.test@example.invalid",
        full_name="Teste de Integracao",
    )

    def workbook(product):
        return create_workbook(
            rows=[
                {
                    "item": TEST_ITEM,
                    "product": product,
                    "obu": "NW1",
                    "owner": "gabriel.duarte",
                    "item_type": "MEC",
                    "eco_type": "REGULAR",
                    "change_bom": "YES",
                    "status": "RELEASED",
                    "receb": "NORMAL",
                    "eco": TEST_ECO,
                    "change_reason": "Teste automatizado",
                    "hq_eco_release_date": date(2026, 1, 2),
                    "az_eco_register_date": date(2026, 1, 5),
                }
            ]
        )

    with db_engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                existing = db.scalar(
                    select(func.count())
                    .select_from(Eco)
                    .where(Eco.item == TEST_ITEM)
                )
                if existing:
                    pytest.fail(
                        "ITEM de teste ja existe. Execucao bloqueada."
                    )

                service = EcoImportService(db=db, user=user)

                first = service.import_file(
                    workbook("PRODUTO-ANTIGO"),
                    "integracao.xlsx",
                )
                assert first["imported_rows"] == 1

                second = service.import_file(
                    workbook("PRODUTO-NOVO"),
                    "integracao.xlsx",
                )
                assert second["updated_rows"] == 1

                records = db.scalars(
                    select(Eco).where(Eco.item == TEST_ITEM)
                ).all()

                assert len(records) == 1
                assert records[0].product == "PRODUTO-NOVO"
                assert records[0].au == "GLZ"
                assert records[0].group_name == "BOM"

                history = db.scalars(
                    select(EcoHistory).where(
                        EcoHistory.item == TEST_ITEM,
                        EcoHistory.field_key == "product",
                        EcoHistory.action == "updated",
                    )
                ).all()

                assert any(
                    record.old_value == "PRODUTO-ANTIGO"
                    and record.new_value == "PRODUTO-NOVO"
                    for record in history
                )
        finally:
            transaction.rollback()


def test_reimport_identical_row_does_not_duplicate(db_engine):
    user = SimpleNamespace(
        role="admin",
        email="integration.test@example.invalid",
        full_name="Teste de Integracao",
    )

    row = {
        "item": 900002,
        "product": "PRODUTO-TESTE",
        "obu": "NW1",
        "owner": "gabriel.duarte",
        "item_type": "MEC",
        "eco_type": "REGULAR",
        "change_bom": "YES",
        "status": "RELEASED",
        "receb": "NORMAL",
        "eco": "ECO-TEST-INTEGRATION-002",
        "change_reason": "Teste automatizado",
        "hq_eco_release_date": date(2026, 1, 2),
        "az_eco_register_date": date(2026, 1, 5),
    }

    with db_engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                assert db.scalar(
                    select(func.count()).select_from(Eco)
                    .where(Eco.item == 900002)
                ) == 0

                service = EcoImportService(db=db, user=user)
                data = create_workbook(rows=[row])

                first = service.import_file(data, "integracao.xlsx")
                assert first["imported_rows"] == 1

                with pytest.raises(HTTPException) as error:
                    service.import_file(data, "integracao.xlsx")

                assert error.value.status_code == 409

                assert db.scalar(
                    select(func.count()).select_from(Eco)
                    .where(Eco.item == 900002)
                ) == 1

        finally:
            transaction.rollback()


def test_reimport_item_with_different_eco_is_conflict(db_engine):
    user = SimpleNamespace(
        role="admin",
        email="integration.test@example.invalid",
        full_name="Teste de Integracao",
    )

    row = {
        "item": 900003,
        "product": "PRODUTO-ORIGINAL",
        "obu": "NW1",
        "owner": "gabriel.duarte",
        "item_type": "MEC",
        "eco_type": "REGULAR",
        "change_bom": "YES",
        "status": "RELEASED",
        "receb": "NORMAL",
        "eco": "ECO-TEST-INTEGRATION-003",
        "change_reason": "Teste automatizado",
        "hq_eco_release_date": date(2026, 1, 2),
        "az_eco_register_date": date(2026, 1, 5),
    }

    with db_engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                assert db.scalar(
                    select(func.count()).select_from(Eco)
                    .where(Eco.item == 900003)
                ) == 0

                service = EcoImportService(db=db, user=user)

                first = service.import_file(
                    create_workbook(rows=[row]),
                    "integracao.xlsx",
                )
                assert first["imported_rows"] == 1

                conflicting_row = {
                    **row,
                    "eco": "ECO-DIFERENTE-003",
                    "product": "PRODUTO-ALTERADO",
                }

                with pytest.raises(HTTPException) as error:
                    service.import_file(
                        create_workbook(rows=[conflicting_row]),
                        "integracao.xlsx",
                    )

                assert error.value.status_code == 422

                existing = db.scalar(
                    select(Eco).where(Eco.item == 900003)
                )

                assert existing is not None
                assert existing.eco == "ECO-TEST-INTEGRATION-003"
                assert existing.product == "PRODUTO-ORIGINAL"

        finally:
            transaction.rollback()
