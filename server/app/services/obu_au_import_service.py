import re
from collections import defaultdict
from io import BytesIO
from zipfile import BadZipFile

from fastapi import HTTPException
from openpyxl import load_workbook
from openpyxl.utils.exceptions import (
    InvalidFileException,
)
from sqlalchemy.exc import IntegrityError

from app.models.entities import (
    ObuAuMapping,
)
from app.repository.settings_repository import (
    SettingsRepository,
)


class ObuAuImportService:

    VALID_OBUS = {
        "NW1",
        "NW4",
        "NW5",
        "NW9",
        "NWD",
        "NWE",
        "NWH",
        "NWK",
        "NWU",
        "NWV",
        "NWW",
        "NWX",
        "NWZ",
        "NYE",
    }

    VALID_AUS = {
        "GLZ",
        "GMZ",
        "LMZ",
        "PNZ",
        "PGZ",
    }

    MAX_FILE_BYTES = (
        25 * 1024 * 1024
    )

    def __init__(
        self,
        db,
    ):
        self.db = db

        self.repository = (
            SettingsRepository(
                db
            )
        )

    def preview_file(
        self,
        content,
        filename,
    ):
        return self._analyze_file(
            content,
            filename,
        )

    def import_file(
        self,
        content,
        filename,
    ):
        preview = self._analyze_file(
            content,
            filename,
        )

        if (
            preview["error_rows"]
            or preview["conflict_rows"]
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "message": (
                        "Corrija os erros e conflitos "
                        "da planilha antes de importar. "
                        "Nenhuma relação foi alterada."
                    ),
                    "preview": preview,
                },
            )

        new_rows = [
            row
            for row in preview["rows"]
            if row["status"] == "NOVO"
        ]

        update_rows = [
            row
            for row in preview["rows"]
            if row["status"] == "ATUALIZAR"
        ]

        if (
            not new_rows
            and not update_rows
        ):
            return {
                "imported_rows": 0,
                "updated_rows": 0,
                "duplicate_rows":
                    preview["duplicate_rows"],
            }

        try:

            # ---------------------------------------------
            # NOVAS RELAÇÕES
            # ---------------------------------------------

            for row in new_rows:

                self.repository.create_obu_au(
                    ObuAuMapping(
                        obu=row["obu"],
                        au=row["au"],
                    )
                )

            # ---------------------------------------------
            # ATUALIZAÇÕES
            # ---------------------------------------------

            for row in update_rows:

                existing = (
                    self.repository
                    .get_obu_au_by_obu(
                        row["obu"]
                    )
                )

                if not existing:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "As relações OBU → AU "
                            "foram alteradas durante "
                            "a importação. Analise "
                            "o arquivo novamente."
                        ),
                    )

                existing.au = (
                    row["au"]
                )

            self.db.commit()

        except IntegrityError as error:

            self.db.rollback()

            raise HTTPException(
                status_code=409,
                detail=(
                    "As relações OBU → AU "
                    "foram alteradas durante "
                    "a importação. Analise "
                    "o arquivo novamente."
                ),
            ) from error

        except Exception:

            self.db.rollback()

            raise

        return {
            "imported_rows":
                len(new_rows),

            "updated_rows":
                len(update_rows),

            "duplicate_rows":
                preview["duplicate_rows"],
        }

    def _analyze_file(
        self,
        content,
        filename,
    ):

        # ---------------------------------------------
        # ARQUIVO
        # ---------------------------------------------

        if (
            not filename
            or not filename
            .lower()
            .endswith(".xlsx")
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Formato inválido. "
                    "Envie um arquivo .xlsx."
                ),
            )

        if not content:
            raise HTTPException(
                status_code=400,
                detail=(
                    "O arquivo enviado está vazio."
                ),
            )

        if (
            len(content)
            > self.MAX_FILE_BYTES
        ):
            raise HTTPException(
                status_code=413,
                detail=(
                    "O arquivo excede o "
                    "limite máximo de 25 MB."
                ),
            )

        workbook = None

        try:

            workbook = load_workbook(
                BytesIO(content),
                read_only=True,
                data_only=True,
            )

            worksheet = (
                workbook.active
            )

            rows = (
                worksheet
                .iter_rows(
                    values_only=True
                )
            )

            header = next(
                rows,
                None,
            )

        except (
            BadZipFile,
            InvalidFileException,
            OSError,
            ValueError,
            KeyError,
        ) as error:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Não foi possível ler "
                    "o arquivo XLSX enviado."
                ),
            ) from error

        try:

            # -----------------------------------------
            # CABEÇALHO
            # -----------------------------------------

            if not header:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A planilha não contém "
                        "as colunas OBU e AU."
                    ),
                )

            header_positions = {}

            for (
                index,
                value,
            ) in enumerate(
                header
            ):

                name = (
                    self._clean_text(
                        value
                    )
                    .upper()
                )

                if (
                    name
                    in {
                        "OBU",
                        "AU",
                    }
                    and name
                    not in header_positions
                ):
                    header_positions[
                        name
                    ] = index

            if not {
                "OBU",
                "AU",
            }.issubset(
                header_positions
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A planilha precisa "
                        "conter as colunas "
                        "OBU e AU."
                    ),
                )

            # -----------------------------------------
            # LINHAS
            # -----------------------------------------

            parsed_rows = []

            for (
                excel_row,
                values,
            ) in enumerate(
                rows,
                start=2,
            ):

                obu_value = (
                    self._value_at(
                        values,
                        header_positions[
                            "OBU"
                        ],
                    )
                )

                au_value = (
                    self._value_at(
                        values,
                        header_positions[
                            "AU"
                        ],
                    )
                )

                if (
                    not self._clean_text(
                        obu_value
                    )
                    and
                    not self._clean_text(
                        au_value
                    )
                ):
                    continue

                obu = (
                    self._clean_text(
                        obu_value
                    )
                    .upper()
                )

                au = (
                    self._clean_text(
                        au_value
                    )
                    .upper()
                )

                errors = []

                if not obu:
                    errors.append(
                        "OBU vazio."
                    )

                elif (
                    obu
                    not in self.VALID_OBUS
                ):
                    errors.append(
                        f"OBU inválido: {obu}."
                    )

                if not au:
                    errors.append(
                        "AU vazio."
                    )

                elif (
                    au
                    not in self.VALID_AUS
                ):
                    errors.append(
                        f"AU inválido: {au}."
                    )

                parsed_rows.append(
                    {
                        "excel_row":
                            excel_row,

                        "obu":
                            obu,

                        "au":
                            au,

                        "status":
                            (
                                "ERRO"
                                if errors
                                else ""
                            ),

                        "message":
                            " ".join(
                                errors
                            ),

                        "_key":
                            obu,
                    }
                )

        finally:

            if workbook:
                workbook.close()

        # ---------------------------------------------
        # AGRUPAR POR OBU
        # ---------------------------------------------

        valid_by_obu = defaultdict(
            list
        )

        for row in parsed_rows:

            if not row["status"]:

                valid_by_obu[
                    row["_key"]
                ].append(
                    row
                )

        # ---------------------------------------------
        # BANCO ATUAL
        # ---------------------------------------------

        existing_by_obu = {
            self._clean_text(
                item.obu
            ).upper():
                self._clean_text(
                    item.au
                ).upper()

            for item
            in self.repository.all_obu_au()
        }

        # ---------------------------------------------
        # CLASSIFICAR
        # ---------------------------------------------

        for (
            obu,
            obu_rows,
        ) in valid_by_obu.items():

            file_aus = {
                row["au"]
                for row
                in obu_rows
            }

            # Mesmo OBU com AUs diferentes
            # na mesma planilha.
            if len(file_aus) > 1:

                for row in obu_rows:

                    row["status"] = (
                        "CONFLITO"
                    )

                    row["message"] = (
                        "O mesmo OBU aparece "
                        "no arquivo com AUs "
                        "diferentes."
                    )

                continue

            au = next(
                iter(file_aus)
            )

            existing_au = (
                existing_by_obu
                .get(obu)
            )

            # -----------------------------------------
            # NÃO EXISTE NO BANCO
            # -----------------------------------------

            if existing_au is None:

                obu_rows[0][
                    "status"
                ] = "NOVO"

                obu_rows[0][
                    "message"
                ] = (
                    "Nova relação OBU → AU."
                )

            # -----------------------------------------
            # JÁ EXISTE IGUAL
            # -----------------------------------------

            elif (
                existing_au
                == au
            ):

                obu_rows[0][
                    "status"
                ] = "DUPLICADO"

                obu_rows[0][
                    "message"
                ] = (
                    "Relação já cadastrada."
                )

            # -----------------------------------------
            # EXISTE, MAS AU MUDOU
            # -----------------------------------------

            else:

                obu_rows[0][
                    "status"
                ] = "ATUALIZAR"

                obu_rows[0][
                    "message"
                ] = (
                    f"AU atual: "
                    f"{existing_au}. "
                    f"Novo AU: {au}."
                )

            # Repetições iguais dentro
            # do mesmo arquivo.
            for row in obu_rows[1:]:

                row["status"] = (
                    "DUPLICADO"
                )

                row["message"] = (
                    "OBU repetido no "
                    "arquivo com o mesmo AU."
                )

        # ---------------------------------------------
        # CONTADORES
        # ---------------------------------------------

        statuses = (
            "NOVO",
            "ATUALIZAR",
            "DUPLICADO",
            "CONFLITO",
            "ERRO",
        )

        counts = {
            status: sum(
                row["status"]
                == status
                for row
                in parsed_rows
            )
            for status
            in statuses
        }

        for row in parsed_rows:
            row.pop(
                "_key",
                None,
            )

        return {
            "total_rows":
                len(parsed_rows),

            "new_rows":
                counts["NOVO"],

            "update_rows":
                counts["ATUALIZAR"],

            "duplicate_rows":
                counts["DUPLICADO"],

            "conflict_rows":
                counts["CONFLITO"],

            "error_rows":
                counts["ERRO"],

            "can_import":
                (
                    counts["ERRO"] == 0
                    and
                    counts[
                        "CONFLITO"
                    ] == 0
                    and
                    (
                        counts["NOVO"] > 0
                        or
                        counts[
                            "ATUALIZAR"
                        ] > 0
                    )
                ),

            "rows":
                parsed_rows,
        }

    @staticmethod
    def _value_at(
        values,
        index,
    ):
        return (
            values[index]
            if index < len(values)
            else None
        )

    @staticmethod
    def _clean_text(
        value,
    ):
        if value is None:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value).strip(),
        )