import io

from datetime import date
from types import SimpleNamespace

import pytest

from fastapi import HTTPException

from openpyxl import Workbook

from app.services.eco_import_service import (
    EcoImportService,
)


# =========================================================
# CABEÇALHOS REAIS DA CTRL GERAL
# =========================================================

CTRL_GERAL_HEADERS = {
    1: "GAP",
    2: "ITEM",
    3: "MONTH",
    4: "PRODUCT",
    5: "AU",
    6: "OBU",
    7: "GROUP",
    8: "OWNER",
    9: "ITEM TYPE",
    10: "ECO TYPE",
    11: "Change BOM?",
    12: "STATUS",
    13: "RECEB.",
    14: "ECO",
    15: "CHANGE REASON",
    16: "HQ ECO RELEASE DATE",
    17: "AZ ECO REGISTER DATE",
    18: "Auto ECR?",
    19: "1-Delay ECO Register",
    20: "ECO registration week",
    21: "Council meeting Week",

    22: "HZ/IN/KR\nECO(1)",
    23: "HZ/IN/KR\nRECEIVE DATE (1)",
    24: "ECO Origem (1)",

    25: "HZ/IN/KR\nECO(2)",
    26: "HZ/SH/IN\nRECEIVE DATE (2)",
    27: "ECO Origem (2)",

    28: "HZ/IN/KR\nECO(3)",
    29: "HZ/SH/IN\nRECEIVE DATE (3)",
    30: "ECO Origem (3)",

    31: "AZ_ECO_NO.",
    32: "Change reason2",
    33: "Change BOM?",
    34: "AZ ECO CREATION DATE",
    35: "GAP Start AZ ECO",
    36: "Contar Eco emitida > 1 dias",
    37: "GAP AGREEMENT",

    38: "AGREEMENT\nOTHER\nDEPTS START\n(1)",
    39: "AGREEMENT\nOTHER\nDEPTS FINSHI\n(1)",
    40: "GAP AGREEMENT\nOTHER\nDEPTS (1)",

    41: "AGREEMENT\nOTHER\nDEPTS START\n(2)",
    42: "AGREEMENT\nOTHER\nDEPTS FINSHI\n(2)",
    43: "GAP AGREEMENT\nOTHER\nDEPTS (2)",

    44: "AGREEMENT\nOTHER\nDEPTS START\n(3)",
    45: "AGREEMENT\nOTHER\nDEPTS FINSHI\n(3)",
    46: "GAP AGREEMENT\nOTHER\nDEPTS (3)",

    47: "GAP TOTAL AGREEMENT\nOTHER\nDEPTS",

    48: "2ST APROV R&D",
    49: "2ST APROV R&D START (1)",
    50: "2ST APROV R&D FINISH (1)",
    51: "GAP 2ST APROV R&D (1)",

    52: "2ST APROV R&D START (2)",
    53: "2ST APROV R&D FINISH (2)",
    54: "GAP 2ST APROV R&D (2)",
    55: "GAP TOTAL 2ST APROV R&D",

    56: "ECO release week",
    57: "AZ Gap",
    58: "Contar Eco concluída > 7 dias",
    59: "Contar Eco concluída > 10 dias",
    60: "Total Gap",
    61: "RELEASE MONTH",
    62: "RELEASE YEAR",

    63: "CHANGE REASON",
    64: "MODEL",
    65: "New Model?\n(Check in NPI plan 26Y)",
    66: (
        "Origem approval\n"
        "(mandatory for local and AV ECO)"
    ),
    67: "Event",
    68: "COMMENTS",

    69: "SET ECO",
    70: "SET ECO REGISTER DATE",
    71: "SET ECO RELEASE DATE",
    72: "CHANGE REASON",
    73: "MODEL",
}


# =========================================================
# HELPERS
# =========================================================

def create_service(
    existing=None,
    obu_map=None,
    owner_map=None,
):
    user = SimpleNamespace(
        role="admin",
        email="admin@eco.com",
        full_name="Administrador",
    )


    service = EcoImportService(
        db=None,
        user=user,
    )


    service._settings_maps = lambda: (
        obu_map
        or {
            "NW1": "GLZ",
        },

        owner_map
        or {
            "owner.test": "BOM",
        },
    )


    service._existing_ecos = (
        lambda eco_codes:
            existing
            or {}
    )


    return service


def create_workbook(
    *,
    sheet_name="CTRL GERAL",
    rows=None,
):
    workbook = Workbook()


    worksheet = (
        workbook.active
    )


    worksheet.title = (
        sheet_name
    )


    # -----------------------------------------------------
    # CABEÇALHO REAL NA LINHA 7
    # -----------------------------------------------------

    header_row = 7


    for (
        column,
        value,
    ) in CTRL_GERAL_HEADERS.items():

        worksheet.cell(
            row=header_row,
            column=column,
            value=value,
        )


    # -----------------------------------------------------
    # DADOS
    # -----------------------------------------------------

    if rows is None:

        rows = [
            {
                "item": 1,

                "product": "AAA",

                "obu": "NW1",

                "owner":
                    "owner.test",

                "item_type":
                    "MEC",

                "eco_type":
                    "REGULAR",

                "change_bom":
                    "YES",

                "status":
                    "RELEASED",

                "receb":
                    "NORMAL",

                "eco":
                    "ECO-001",

                "change_reason":
                    "Alteração teste",

                "hq_eco_release_date":
                    date(
                        2026,
                        1,
                        2,
                    ),

                "az_eco_register_date":
                    date(
                        2026,
                        1,
                        5,
                    ),

                "auto_ecr":
                    "NO",

                "az_eco_creation_date":
                    date(
                        2026,
                        1,
                        6,
                    ),

                "second_aprov_rd":
                    "R&D",

                "second_aprov_rd_start_1":
                    date(
                        2026,
                        1,
                        7,
                    ),

                "second_aprov_rd_finish_1":
                    date(
                        2026,
                        1,
                        12,
                    ),

                "comments":
                    "Teste de importação",
            }
        ]


    field_to_column = {
        spec["field"]: column

        for (
            column,
            spec,
        ) in (
            EcoImportService
            .COLUMN_SPECS
            .items()
        )
    }


    current_row = 8


    for data in rows:

        worksheet.cell(
            row=current_row,
            column=2,
            value=data.get(
                "item"
            ),
        )


        for (
            field,
            value,
        ) in data.items():

            if field == "item":
                continue


            column = (
                field_to_column.get(
                    field
                )
            )


            if column is None:
                continue


            worksheet.cell(
                row=current_row,
                column=column,
                value=value,
            )


        current_row += 1


    output = io.BytesIO()


    workbook.save(
        output
    )


    workbook.close()


    return output.getvalue()


# =========================================================
# ESTRUTURA DAS COLUNAS
# =========================================================

def test_rd_columns_match_ctrl_geral():

    specs = (
        EcoImportService
        .COLUMN_SPECS
    )


    assert (
        specs[48]["field"]
        ==
        "second_aprov_rd"
    )


    assert (
        specs[49]["field"]
        ==
        "second_aprov_rd_start_1"
    )


    assert (
        specs[50]["field"]
        ==
        "second_aprov_rd_finish_1"
    )


    assert (
        specs[52]["field"]
        ==
        "second_aprov_rd_start_2"
    )


    assert (
        specs[53]["field"]
        ==
        "second_aprov_rd_finish_2"
    )


# =========================================================
# PREVIEW DE UMA ECO NOVA
# =========================================================

def test_preview_new_eco():

    service = (
        create_service()
    )


    file_bytes = (
        create_workbook()
    )


    result = (
        service.preview(
            file_bytes,
            "controle.xlsx",
        )
    )


    assert (
        result["sheet"]
        ==
        "CTRL GERAL"
    )


    assert (
        result["header_row"]
        == 7
    )


    assert (
        result["total_rows"]
        == 1
    )


    assert (
        result["valid_rows"]
        == 1
    )


    assert (
        result["new_rows"]
        == 1
    )


    assert (
        result["update_rows"]
        == 0
    )


    assert (
        result["error_rows"]
        == 0
    )


    assert (
        result["can_import"]
        is True
    )


    row = (
        result["rows"][0]
    )


    assert (
        row["action"]
        ==
        "NEW"
    )


    assert (
        row["source_item"]
        == 1
    )


    assert (
        row["eco"]
        ==
        "ECO-001"
    )


    assert (
        row["data"]["obu"]
        ==
        "NW1"
    )


    assert (
        row["derived"]["au"]
        ==
        "GLZ"
    )


    assert (
        row["derived"]["group"]
        ==
        "BOM"
    )


    assert (
        row["derived"]["month"]
        ==
        "JAN"
    )


# =========================================================
# CAMPOS CALCULADOS
# =========================================================

def test_preview_recalculates_fields():

    service = (
        create_service()
    )


    result = (
        service.preview(
            create_workbook(),
            "controle.xlsx",
        )
    )


    derived = (
        result[
            "rows"
        ][0][
            "derived"
        ]
    )


    assert (
        derived["gap"]
        ==
        "OK"
    )


    assert (
        derived[
            "delay_eco_register"
        ]
        == 3
    )


    assert (
        derived[
            "gap_start_az_eco"
        ]
        == 1
    )


    # 05/01/2026 até 12/01/2026
    # = 6 dias úteis.

    assert (
        derived["az_gap"]
        == 6
    )


    assert (
        derived[
            "contar_eco_7"
        ]
        is False
    )


# =========================================================
# ECO JÁ EXISTENTE
# =========================================================

def test_preview_existing_eco_is_update():

    service = (
        create_service(
            existing={
                "ECO-001": {
                    "id":
                        "123456",

                    "item":
                        55,
                }
            }
        )
    )


    result = (
        service.preview(
            create_workbook(),
            "controle.xlsx",
        )
    )


    assert (
        result["new_rows"]
        == 0
    )


    assert (
        result["update_rows"]
        == 1
    )


    row = (
        result["rows"][0]
    )


    assert (
        row["action"]
        ==
        "UPDATE"
    )


    assert (
        row["existing"]["item"]
        == 55
    )


# =========================================================
# DUPLICIDADE NO PRÓPRIO XLSX
# =========================================================

def test_preview_duplicate_eco_in_file():

    rows = [
        {
            "item":
                1,

            "obu":
                "NW1",

            "owner":
                "owner.test",

            "item_type":
                "MEC",

            "eco_type":
                "REGULAR",

            "status":
                "WORKING",

            "eco":
                "ECO-DUPLICADA",

            "az_eco_register_date":
                date(
                    2026,
                    1,
                    5,
                ),
        },

        {
            "item":
                2,

            "obu":
                "NW1",

            "owner":
                "owner.test",

            "item_type":
                "MEC",

            "eco_type":
                "REGULAR",

            "status":
                "WORKING",

            "eco":
                "ECO-DUPLICADA",

            "az_eco_register_date":
                date(
                    2026,
                    1,
                    6,
                ),
        },
    ]


    service = (
        create_service()
    )


    result = (
        service.preview(
            create_workbook(
                rows=rows
            ),
            "controle.xlsx",
        )
    )


    assert (
        result["total_rows"]
        == 2
    )


    assert (
        result["new_rows"]
        == 1
    )


    assert (
        result["error_rows"]
        == 1
    )


    assert (
        result["can_import"]
        is False
    )


    assert (
        result["rows"][0]["action"]
        ==
        "NEW"
    )


    assert (
        result["rows"][1]["action"]
        ==
        "ERROR"
    )


    assert any(
        "duplicada"
        in error.lower()

        for error
        in result[
            "rows"
        ][1][
            "errors"
        ]
    )


# =========================================================
# OBU SEM MAPEAMENTO
# =========================================================

def test_preview_requires_obu_mapping():

    rows = [
        {
            "item":
                1,

            "obu":
                "NW9",

            "owner":
                "owner.test",

            "item_type":
                "MEC",

            "eco_type":
                "REGULAR",

            "status":
                "WORKING",

            "eco":
                "ECO-NW9",

            "az_eco_register_date":
                date(
                    2026,
                    1,
                    5,
                ),
        }
    ]


    service = (
        create_service(
            obu_map={
                "NW1":
                    "GLZ",
            }
        )
    )


    result = (
        service.preview(
            create_workbook(
                rows=rows
            ),
            "controle.xlsx",
        )
    )


    assert (
        result["error_rows"]
        == 1
    )


    assert (
        result["can_import"]
        is False
    )


    assert any(
        "OBU"
        in error

        for error
        in result[
            "rows"
        ][0][
            "errors"
        ]
    )


# =========================================================
# OWNER SEM MAPEAMENTO
# =========================================================

def test_preview_requires_owner_mapping():

    rows = [
        {
            "item":
                1,

            "obu":
                "NW1",

            "owner":
                "owner.inexistente",

            "item_type":
                "MEC",

            "eco_type":
                "REGULAR",

            "status":
                "WORKING",

            "eco":
                "ECO-OWNER",

            "az_eco_register_date":
                date(
                    2026,
                    1,
                    5,
                ),
        }
    ]


    service = (
        create_service(
            owner_map={
                "owner.test":
                    "BOM",
            }
        )
    )


    result = (
        service.preview(
            create_workbook(
                rows=rows
            ),
            "controle.xlsx",
        )
    )


    assert (
        result["error_rows"]
        == 1
    )


    assert any(
        "Owner"
        in error

        for error
        in result[
            "rows"
        ][0][
            "errors"
        ]
    )


# =========================================================
# ABA OBRIGATÓRIA
# =========================================================

def test_preview_requires_ctrl_geral():

    service = (
        create_service()
    )


    with pytest.raises(
        HTTPException
    ) as exc:

        service.preview(
            create_workbook(
                sheet_name="OUTRA ABA"
            ),
            "controle.xlsx",
        )


    assert (
        exc.value.status_code
        == 422
    )


    assert (
        "CTRL GERAL"
        in str(
            exc.value.detail
        )
    )


# =========================================================
# EXTENSÃO
# =========================================================

def test_preview_rejects_non_xlsx():

    service = (
        create_service()
    )


    with pytest.raises(
        HTTPException
    ) as exc:

        service.preview(
            b"arquivo",
            "controle.csv",
        )


    assert (
        exc.value.status_code
        == 422
    )


# =========================================================
# ECO OBRIGATÓRIA
# =========================================================

def test_preview_requires_eco_code():

    rows = [
        {
            "item":
                1,

            "obu":
                "NW1",

            "owner":
                "owner.test",

            "item_type":
                "MEC",

            "eco_type":
                "REGULAR",

            "status":
                "WORKING",

            "eco":
                None,

            "az_eco_register_date":
                date(
                    2026,
                    1,
                    5,
                ),
        }
    ]


    service = (
        create_service()
    )


    result = (
        service.preview(
            create_workbook(
                rows=rows
            ),
            "controle.xlsx",
        )
    )


    assert (
        result["error_rows"]
        == 1
    )


    assert (
        result["rows"][0]["action"]
        ==
        "ERROR"
    )


    assert any(
        "ECO está vazia"
        in error

        for error
        in result[
            "rows"
        ][0][
            "errors"
        ]
    )