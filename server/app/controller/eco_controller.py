import io
import json

from datetime import (
    date,
    datetime,
)

from uuid import UUID

import xlsxwriter

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from fastapi.responses import (
    StreamingResponse,
)

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.schemas.eco import (
    EcoCreate,
    EcoUpdate,
)

from app.services.eco_service import (
    EcoService,
)

from app.utils.security import (
    current_user,
)


router = APIRouter(
    prefix="/ecos",
    tags=["ECOs"],
)


# =========================================================
# CONFIGURAÇÃO DA EXPORTAÇÃO
# =========================================================

EXPORT_GROUPS = [
    {
        "label": "IDENTIFICAÇÃO",
        "color": "#595959",
        "font_color": "#FFFFFF",
        "columns": [
            ("gap", "GAP", 11, "text"),
            ("item", "ITEM", 9, "number"),
            ("month", "MONTH", 10, "text"),
            ("product", "Product", 20, "text"),
            ("au", "AU", 10, "text"),
            ("obu", "OBU", 10, "text"),
        ],
    },
    {
        "label": "CLASSIFICAÇÃO",
        "color": "#6B6B6B",
        "font_color": "#FFFFFF",
        "columns": [
            ("group", "GROUP", 12, "text"),
            ("owner", "OWNER", 25, "text"),
            ("item_type", "ITEM TYPE", 14, "text"),
            ("eco_type", "ECO TYPE", 26, "text"),
            ("change_bom", "CHANGE BOM?", 15, "text"),
            ("status", "STATUS", 26, "text"),
            ("receb", "RECEB.", 14, "text"),
        ],
    },
    {
        "label": "ECO HQ",
        "color": "#7F7F7F",
        "font_color": "#FFFFFF",
        "columns": [
            ("eco", "ECO", 18, "text"),
            ("change_reason", "CHANGE REASON", 38, "text"),
            (
                "hq_eco_release_date",
                "HQ ECO RELEASE DATE",
                19,
                "date",
            ),
            (
                "az_eco_register_date",
                "AZ ECO REGISTER DATE",
                19,
                "date",
            ),
            ("auto_ecr", "Auto ECR?", 13, "text"),
            (
                "delay_eco_register",
                "1-Delay ECO Register",
                18,
                "number",
            ),
            (
                "eco_registration_week",
                "ECO REGISTRATION WEEK",
                21,
                "text",
            ),
            (
                "council_meeting_week",
                "Council meeting Week",
                21,
                "text",
            ),
        ],
    },
    {
        "label": "ORIGEM",
        "color": "#A6A6A6",
        "font_color": "#000000",
        "columns": [
            (
                "hz_in_kr_eco_1",
                "HZ/IN/KR ECO(1)",
                18,
                "text",
            ),
            (
                "hz_sh_in_receive_date_1",
                "HZ/SH/IN RECEIVE DATE (1)",
                22,
                "date",
            ),
            (
                "eco_origem_1",
                "ECO Origem (1)",
                16,
                "number",
            ),
            (
                "hz_in_kr_eco_2",
                "HZ/IN/KR ECO(2)",
                18,
                "text",
            ),
            (
                "hz_sh_in_receive_date_2",
                "HZ/SH/IN RECEIVE DATE (2)",
                22,
                "date",
            ),
            (
                "eco_origem_2",
                "ECO Origem (2)",
                16,
                "number",
            ),
            (
                "hz_in_kr_eco_3",
                "HZ/IN/KR ECO(3)",
                18,
                "text",
            ),
            (
                "hz_sh_in_receive_date_3",
                "HZ/SH/IN RECEIVE DATE (3)",
                22,
                "date",
            ),
            (
                "eco_origem_3",
                "ECO Origem (3)",
                16,
                "number",
            ),
        ],
    },
    {
        "label": "AZ ECO",
        "color": "#F4B183",
        "font_color": "#000000",
        "columns": [
            (
                "az_eco_no",
                "AZ_ECO_NO.",
                18,
                "text",
            ),
            (
                "change_reason2",
                "Change reason2",
                38,
                "text",
            ),
            (
                "change_bom_az",
                "Change BOM? AZ",
                17,
                "text",
            ),
            (
                "az_eco_creation_date",
                "AZ ECO CREATION DATE",
                21,
                "date",
            ),
            (
                "gap_start_az_eco",
                "GAP Start AZ ECO",
                18,
                "number",
            ),
            (
                "contar_eco_emitida_1_dias",
                "Contar Eco emitida > 1 dias",
                24,
                "bool",
            ),
            (
                "gap_agreement",
                "GAP AGREEMENT",
                18,
                "number",
            ),
        ],
    },
    {
        "label": "AGREEMENT OTHER DEPTS",
        "color": "#9DC3E6",
        "font_color": "#000000",
        "columns": [
            (
                "agreement_start_1",
                "AGREEMENT OTHER DEPTS START (1)",
                26,
                "date",
            ),
            (
                "agreement_finish_1",
                "AGREEMENT OTHER DEPTS FINSHI (1)",
                26,
                "date",
            ),
            (
                "gap_agreement_1",
                "GAP AGREEMENT OTHER DEPTS (1)",
                25,
                "number",
            ),
            (
                "agreement_start_2",
                "AGREEMENT OTHER DEPTS START (2)",
                26,
                "date",
            ),
            (
                "agreement_finish_2",
                "AGREEMENT OTHER DEPTS FINSHI (2)",
                26,
                "date",
            ),
            (
                "gap_agreement_2",
                "GAP AGREEMENT OTHER DEPTS (2)",
                25,
                "number",
            ),
            (
                "agreement_start_3",
                "AGREEMENT OTHER DEPTS START (3)",
                26,
                "date",
            ),
            (
                "agreement_finish_3",
                "AGREEMENT OTHER DEPTS FINSHI (3)",
                26,
                "date",
            ),
            (
                "gap_agreement_3",
                "GAP AGREEMENT OTHER DEPTS (3)",
                25,
                "number",
            ),
            (
                "gap_total_agreement",
                "GAP TOTAL AGREEMENT OTHER DEPTS",
                27,
                "number",
            ),
        ],
    },
    {
        "label": "R&D APPROVAL",
        "color": "#A9D18E",
        "font_color": "#000000",
        "columns": [
            (
                "second_aprov_rd",
                "2ST APROV R&D",
                19,
                "text",
            ),
            (
                "second_aprov_rd_start_1",
                "2ST APROV R&D START (1)",
                23,
                "date",
            ),
            (
                "second_aprov_rd_finish_1",
                "2ST APROV R&D FINISH (1)",
                23,
                "date",
            ),
            (
                "gap_2st_1",
                "GAP 2ST APROV R&D (1)",
                22,
                "number",
            ),
            (
                "second_aprov_rd_start_2",
                "2ST APROV R&D START (2)",
                23,
                "date",
            ),
            (
                "second_aprov_rd_finish_2",
                "2ST APROV R&D FINISH (2)",
                23,
                "date",
            ),
            (
                "gap_2st_2",
                "GAP 2ST APROV R&D (2)",
                22,
                "number",
            ),
            (
                "gap_total_2st",
                "GAP TOTAL 2ST APROV R&D",
                24,
                "number",
            ),
        ],
    },
    {
        "label": "RELEASE",
        "color": "#FFD966",
        "font_color": "#000000",
        "columns": [
            (
                "eco_release_week",
                "ECO release week",
                18,
                "text",
            ),
            (
                "az_gap",
                "AZ Gap",
                12,
                "number",
            ),
            (
                "contar_eco_7",
                "Contar Eco concluída > 7 dias",
                25,
                "bool",
            ),
            (
                "contar_eco_10",
                "Contar Eco concluída > 10 dias",
                26,
                "bool",
            ),
            (
                "total_gap",
                "Total Gap",
                14,
                "number",
            ),
            (
                "release_month",
                "RELEASE MONTH",
                16,
                "text",
            ),
            (
                "release_year",
                "RELEASE YEAR",
                15,
                "text",
            ),
        ],
    },
    {
        "label": "ADICIONAIS",
        "color": "#BDD7EE",
        "font_color": "#000000",
        "columns": [
            (
                "change_reason_az",
                "CHANGE REASON AZ",
                38,
                "text",
            ),
            (
                "model_az",
                "MODEL AZ",
                30,
                "text",
            ),
            (
                "new_model",
                "New Model?(Check in NPI plan 26Y)",
                30,
                "text",
            ),
            (
                "origem_approval",
                "Origem approval",
                20,
                "text",
            ),
            (
                "event",
                "Event",
                12,
                "text",
            ),
            (
                "comments",
                "COMMENTS",
                45,
                "text",
            ),
        ],
    },
    {
        "label": "SET ECO (somente BM/NWK)",
        "color": "#F4B6C2",
        "font_color": "#000000",
        "columns": [
            (
                "set_eco",
                "SET ECO",
                18,
                "text",
            ),
            (
                "set_eco_register_date",
                "SET ECO REGISTER DATE",
                21,
                "date",
            ),
            (
                "set_eco_release_date",
                "SET ECO RELEASE DATE",
                21,
                "date",
            ),
            (
                "set_eco_change_reason",
                "SET ECO CHANGE REASON",
                38,
                "text",
            ),
            (
                "set_eco_model",
                "SET ECO MODEL",
                26,
                "text",
            ),
        ],
    },
]


ALL_EXPORT_KEYS = {
    column[0]
    for group in EXPORT_GROUPS
    for column in group["columns"]
}


# =========================================================
# AUXILIARES
# =========================================================

def _parse_column_filters(
    raw_filters: str | None,
):
    if not raw_filters:
        return {}


    try:
        filters = json.loads(
            raw_filters
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=422,
            detail=(
                "column_filters deve ser "
                "um objeto JSON válido."
            ),
        )


    if not isinstance(
        filters,
        dict,
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "column_filters deve ser "
                "um objeto JSON."
            ),
        )


    parsed = {}


    for key, value in filters.items():

        if (
            key not in
            ALL_EXPORT_KEYS
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Filtro de coluna inválido: {key}"
                ),
            )


        if value is None:
            continue


        normalized = str(
            value
        ).strip()


        if normalized:
            parsed[key] = normalized


    return parsed


def _write_excel_value(
    worksheet,
    row_index,
    column_index,
    value,
    column_type,
    formats,
):
    if (
        value is None
        or
        value == ""
    ):
        worksheet.write_blank(
            row_index,
            column_index,
            None,
            formats["body"],
        )

        return


    if column_type == "bool":

        text = (
            "YES"
            if bool(value)
            else "NO"
        )

        worksheet.write_string(
            row_index,
            column_index,
            text,
            formats["center"],
        )

        return


    if column_type == "date":

        parsed = value


        if isinstance(
            value,
            str,
        ):
            try:
                parsed = (
                    datetime.fromisoformat(
                        value[:10]
                    )
                )

            except ValueError:
                parsed = None


        elif (
            isinstance(value, date)
            and
            not isinstance(
                value,
                datetime,
            )
        ):
            parsed = datetime.combine(
                value,
                datetime.min.time(),
            )


        if isinstance(
            parsed,
            datetime,
        ):
            worksheet.write_datetime(
                row_index,
                column_index,
                parsed,
                formats["date"],
            )

        else:
            worksheet.write_string(
                row_index,
                column_index,
                str(value),
                formats["body"],
            )

        return


    if (
        column_type == "number"
        and
        isinstance(
            value,
            (
                int,
                float,
            ),
        )
        and
        not isinstance(
            value,
            bool,
        )
    ):
        worksheet.write_number(
            row_index,
            column_index,
            value,
            formats["number"],
        )

        return


    text = str(
        value
    )


    worksheet.write_string(
        row_index,
        column_index,
        text,
        formats["body"],
    )


def _build_excel(
    rows,
):
    output = io.BytesIO()


    workbook = xlsxwriter.Workbook(
        output,
        {
            "in_memory": True,
            "remove_timezone": True,
        },
    )


    worksheet = workbook.add_worksheet(
        "CTRL GERAL"
    )


    # -----------------------------------------------------
    # FORMATOS
    # -----------------------------------------------------

    body_format = workbook.add_format(
        {
            "font_name": "Arial",
            "font_size": 9,
            "border": 1,
            "border_color": "#D9D9D9",
            "valign": "vcenter",
        }
    )


    center_format = workbook.add_format(
        {
            "font_name": "Arial",
            "font_size": 9,
            "border": 1,
            "border_color": "#D9D9D9",
            "align": "center",
            "valign": "vcenter",
        }
    )


    number_format = workbook.add_format(
        {
            "font_name": "Arial",
            "font_size": 9,
            "border": 1,
            "border_color": "#D9D9D9",
            "align": "center",
            "valign": "vcenter",
            "num_format": "0",
        }
    )


    date_format = workbook.add_format(
        {
            "font_name": "Arial",
            "font_size": 9,
            "border": 1,
            "border_color": "#D9D9D9",
            "align": "center",
            "valign": "vcenter",
            "num_format": "dd/mm/yyyy",
        }
    )


    formats = {
        "body": body_format,
        "center": center_format,
        "number": number_format,
        "date": date_format,
    }


    # -----------------------------------------------------
    # LINHA DOS GRUPOS
    # -----------------------------------------------------

    current_column = 0


    for group in EXPORT_GROUPS:

        columns = group[
            "columns"
        ]


        start_column = (
            current_column
        )


        end_column = (
            current_column
            +
            len(columns)
            -
            1
        )


        group_format = (
            workbook.add_format(
                {
                    "bold": True,
                    "font_name": "Arial",
                    "font_size": 10,
                    "font_color":
                        group[
                            "font_color"
                        ],
                    "bg_color":
                        group[
                            "color"
                        ],
                    "border": 1,
                    "border_color":
                        "#7F7F7F",
                    "align": "center",
                    "valign": "vcenter",
                }
            )
        )


        if (
            start_column
            ==
            end_column
        ):
            worksheet.write(
                0,
                start_column,
                group["label"],
                group_format,
            )

        else:
            worksheet.merge_range(
                0,
                start_column,
                0,
                end_column,
                group["label"],
                group_format,
            )


        current_column = (
            end_column + 1
        )


    # -----------------------------------------------------
    # CABEÇALHOS
    # -----------------------------------------------------

    current_column = 0


    for group in EXPORT_GROUPS:

        header_format = (
            workbook.add_format(
                {
                    "bold": True,
                    "font_name": "Arial",
                    "font_size": 9,
                    "font_color":
                        group[
                            "font_color"
                        ],
                    "bg_color":
                        group[
                            "color"
                        ],
                    "border": 1,
                    "border_color":
                        "#7F7F7F",
                    "align": "center",
                    "valign": "vcenter",
                    "text_wrap": True,
                }
            )
        )


        for (
            key,
            label,
            width,
            column_type,
        ) in group["columns"]:

            worksheet.write(
                1,
                current_column,
                label,
                header_format,
            )


            worksheet.set_column(
                current_column,
                current_column,
                width,
            )


            current_column += 1


    # -----------------------------------------------------
    # DADOS
    # -----------------------------------------------------

    excel_row = 2


    for row in rows:

        excel_column = 0


        for group in EXPORT_GROUPS:

            for (
                key,
                _label,
                _width,
                column_type,
            ) in group["columns"]:

                value = row.get(
                    key
                )


                _write_excel_value(
                    worksheet,
                    excel_row,
                    excel_column,
                    value,
                    column_type,
                    formats,
                )


                excel_column += 1


        excel_row += 1


    # -----------------------------------------------------
    # VISUAL
    # -----------------------------------------------------

    last_column = (
        len(
            ALL_EXPORT_KEYS
        )
        - 1
    )


    last_row = max(
        1,
        excel_row - 1,
    )


    worksheet.set_row(
        0,
        24,
    )


    worksheet.set_row(
        1,
        44,
    )


    worksheet.freeze_panes(
        2,
        2,
    )


    worksheet.autofilter(
        1,
        0,
        last_row,
        last_column,
    )


    worksheet.hide_gridlines(
        2
    )


    workbook.close()


    output.seek(
        0
    )


    return output


# =========================================================
# LISTAR ECOS
# =========================================================

@router.get("")
def list_ecos(
    page: int = Query(
        default=1,
        ge=1,
    ),

    page_size: int = Query(
        default=50,
        ge=1,
        le=500,
    ),

    search: str | None = None,

    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),

    month: str | None = None,

    group_filter: str | None = Query(
        default=None,
        alias="group",
    ),

    obu: str | None = None,

    item_type: str | None = None,

    eco_type: str | None = None,

    column_filters: str | None = None,

    db: Session = Depends(
        get_db
    ),

    user=Depends(
        current_user
    ),
):
    service = EcoService(
        db,
        user,
    )


    parsed_filters = (
        _parse_column_filters(
            column_filters
        )
    )


    items, total = (
        service.list(
            page=page,
            page_size=page_size,
            search=search,
            status=status_filter,
            month=month,
            group=group_filter,
            obu=obu,
            item_type=item_type,
            eco_type=eco_type,
            column_filters=(
                parsed_filters
            ),
        )
    )


    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# =========================================================
# EXPORTAR XLSX
# =========================================================

@router.get("/export")
def export_ecos(
    search: str | None = None,

    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),

    month: str | None = None,

    group_filter: str | None = Query(
        default=None,
        alias="group",
    ),

    obu: str | None = None,

    item_type: str | None = None,

    eco_type: str | None = None,

    column_filters: str | None = None,

    db: Session = Depends(
        get_db
    ),

    user=Depends(
        current_user
    ),
):
    service = EcoService(
        db,
        user,
    )


    parsed_filters = (
        _parse_column_filters(
            column_filters
        )
    )


    rows = (
        service.list_for_export(
            search=search,
            status=status_filter,
            month=month,
            group=group_filter,
            obu=obu,
            item_type=item_type,
            eco_type=eco_type,
            column_filters=(
                parsed_filters
            ),
        )
    )


    excel_file = (
        _build_excel(
            rows
        )
    )


    current_date = (
        datetime.now()
        .strftime(
            "%Y-%m-%d"
        )
    )


    filename = (
        "ECO_CONTROL_"
        f"{current_date}.xlsx"
    )


    return StreamingResponse(
        excel_file,
        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                (
                    'attachment; '
                    f'filename="{filename}"'
                )
        },
    )


# =========================================================
# CRIAR ECO
# =========================================================

@router.post("")
def create_eco(
    body: EcoCreate,

    db: Session = Depends(
        get_db
    ),

    user=Depends(
        current_user
    ),
):
    service = EcoService(
        db,
        user,
    )


    return service.create(
        body
    )


# =========================================================
# CRIAR ECO ABAIXO DE OUTRA ECO
# =========================================================

@router.post("/{eco_id}/after")
def create_eco_after(
    eco_id: UUID,

    db: Session = Depends(
        get_db
    ),

    user=Depends(
        current_user
    ),
):
    service = EcoService(
        db,
        user,
    )


    return service.create_after(
        eco_id
    )


# =========================================================
# ATUALIZAR ECO
# =========================================================

@router.patch("/{eco_id}")
def update_eco(
    eco_id: UUID,

    body: EcoUpdate,

    db: Session = Depends(
        get_db
    ),

    user=Depends(
        current_user
    ),
):
    service = EcoService(
        db,
        user,
    )


    return service.update(
        eco_id,
        body,
    )


# =========================================================
# EXCLUIR ECO
# =========================================================

@router.delete(
    "/{eco_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
def delete_eco(
    eco_id: UUID,

    db: Session = Depends(
        get_db
    ),

    user=Depends(
        current_user
    ),
):
    service = EcoService(
        db,
        user,
    )


    service.delete(
        eco_id
    )


    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )