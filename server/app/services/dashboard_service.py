from sqlalchemy import (
    select,
    func,
)

from app.models.entities import Eco
from app.utils.eco_calculations import (
    compute_eco_fields,
)


class DashboardService:

    MONTH_ORDER = [
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]


    def __init__(
        self,
        db,
    ):
        self.db = db


    # =====================================================
    # NORMALIZAÇÃO
    # =====================================================

    @staticmethod
    def _normalize_text(
        value,
        default="N/A",
    ):
        """
        Remove espaços extras das pontas
        e também espaços duplicados internos.

        Exemplos:
        ' MEC '      -> 'MEC'
        'MEC  TEAM'  -> 'MEC TEAM'
        '   '         -> 'N/A'
        None          -> 'N/A'
        """

        if value is None:
            return default


        if not isinstance(
            value,
            str,
        ):
            return value


        normalized = " ".join(
            value.split()
        )


        return (
            normalized
            if normalized
            else default
        )


    @classmethod
    def _normalize_month(
        cls,
        value,
    ):
        normalized = (
            cls._normalize_text(
                value,
                default="",
            )
        )

        if not normalized:
            return ""


        return normalized.upper()


    # =====================================================
    # CONSULTA BASE
    # =====================================================

    def _rows(
        self,
        month=None,
    ):
        query = select(Eco)


        if month:

            normalized_month = (
                self._normalize_month(
                    month
                )
            )


            query = query.where(
                func.upper(
                    func.trim(
                        Eco.month
                    )
                )
                ==
                normalized_month
            )


        return (
            self.db
            .scalars(query)
            .all()
        )


    # =====================================================
    # MESES
    # =====================================================

    def months(self):

        values = (
            self.db
            .scalars(
                select(
                    Eco.month
                )
                .where(
                    Eco.month.is_not(
                        None
                    )
                )
            )
            .all()
        )


        normalized_values = {
            self._normalize_month(
                value
            )
            for value
            in values
            if value
        }


        return [
            month
            for month
            in self.MONTH_ORDER
            if month
            in normalized_values
        ]


    # =====================================================
    # CARDS
    # =====================================================

    def stats(self):

        rows = self._rows()


        computed_rows = [
            compute_eco_fields(
                row
            )
            for row
            in rows
        ]


        normalized_statuses = [
            self._normalize_text(
                row.status,
                default="",
            )
            for row
            in rows
        ]


        def count_status(
            status,
        ):
            return sum(
                1
                for current_status
                in normalized_statuses
                if current_status
                == status
            )


        cancelled = sum(
            1
            for current_status
            in normalized_statuses
            if current_status
            in {
                "CANCELLED",
                "TO BE CANCELLED",
            }
        )


        gap7 = sum(
            1
            for calculated
            in computed_rows
            if calculated[
                "contar_eco_7"
            ]
            is True
        )


        gap14 = sum(
            1
            for calculated
            in computed_rows
            if calculated[
                "contar_eco_14"
            ]
            is True
        )


        return {
            "total":
                len(rows),

            "working":
                count_status(
                    "WORKING"
                ),

            "on_hold":
                count_status(
                    "ON HOLD"
                ),

            "processing":
                count_status(
                    "PROCESSING"
                ),

            "released":
                count_status(
                    "RELEASED"
                ),

            "rejected":
                count_status(
                    "REJECTED"
                ),

            "cancelled":
                cancelled,

            # A regra de OVERDUE ainda
            # precisa ser definida pelo P.O.
            "overdue":
                0,

            "gap7":
                gap7,

            # Regra validada:
            # AZ Gap > 14
            "gap14":
                gap14,
        }


    # =====================================================
    # AGRUPAMENTOS
    # =====================================================

    def group(
        self,
        dimension,
        month=None,
    ):

        mapping = {
            "status":
                Eco.status,

            "group":
                Eco.group_name,

            "owner":
                Eco.owner,

            "obu":
                Eco.obu,

            "au":
                Eco.au,

            "eco_type":
                Eco.eco_type,
        }


        column = mapping[
            dimension
        ]


        query = (
            select(
                column,
                func.count(
                    Eco.id
                ),
            )
            .group_by(
                column
            )
        )


        if month:

            normalized_month = (
                self._normalize_month(
                    month
                )
            )


            query = query.where(
                func.upper(
                    func.trim(
                        Eco.month
                    )
                )
                ==
                normalized_month
            )


        merged = {}


        for (
            name,
            value,
        ) in self.db.execute(
            query
        ).all():

            normalized_name = (
                self._normalize_text(
                    name
                )
            )


            merged[
                normalized_name
            ] = (
                merged.get(
                    normalized_name,
                    0,
                )
                +
                value
            )


        return [
            {
                "name":
                    name,

                "value":
                    value,
            }
            for (
                name,
                value,
            )
            in sorted(
                merged.items(),
                key=lambda item:
                    item[1],
                reverse=True,
            )
        ]


    # =====================================================
    # EVOLUÇÃO POR MÊS
    # =====================================================

    def evolution(self):

        grouped = {
            item["name"]:
                item["value"]
            for item
            in self.group_by_month()
        }


        return [
            {
                "name":
                    month,

                "value":
                    grouped[
                        month
                    ],
            }
            for month
            in self.MONTH_ORDER
            if month
            in grouped
        ]


    # =====================================================
    # AGRUPAMENTO POR MÊS
    # =====================================================

    def group_by_month(self):

        rows = (
            self.db
            .execute(
                select(
                    Eco.month,
                    func.count(
                        Eco.id
                    ),
                )
                .group_by(
                    Eco.month
                )
            )
            .all()
        )


        merged = {}


        for (
            month,
            value,
        ) in rows:

            normalized_month = (
                self._normalize_month(
                    month
                )
            )


            if not normalized_month:
                normalized_month = (
                    "N/A"
                )


            merged[
                normalized_month
            ] = (
                merged.get(
                    normalized_month,
                    0,
                )
                +
                value
            )


        return [
            {
                "name":
                    name,

                "value":
                    value,
            }
            for (
                name,
                value,
            )
            in merged.items()
        ]


    # =====================================================
    # TEMPO DE ATRASO
    # =====================================================

    def delay(
        self,
        month=None,
    ):

        categories = {
            "No prazo":
                0,

            "1-7 dias":
                0,

            "8-14 dias":
                0,

            "> 14 dias":
                0,
        }


        for row in self._rows(
            month
        ):

            gap = (
                compute_eco_fields(
                    row
                )[
                    "az_gap"
                ]
            )


            if (
                gap is None
                or
                gap <= 0
            ):

                categories[
                    "No prazo"
                ] += 1


            elif gap <= 7:

                categories[
                    "1-7 dias"
                ] += 1


            elif gap <= 14:

                categories[
                    "8-14 dias"
                ] += 1


            else:

                categories[
                    "> 14 dias"
                ] += 1


        return [
            {
                "name":
                    name,

                "value":
                    value,
            }
            for (
                name,
                value,
            )
            in categories.items()
        ]


    # =====================================================
    # RESUMO MENSAL
    # =====================================================

    def monthly_summary(self):

        result = []


        for month in self.MONTH_ORDER:

            rows = self._rows(
                month
            )


            if not rows:
                continue


            statuses = [
                self._normalize_text(
                    row.status,
                    default="",
                )
                for row
                in rows
            ]


            result.append(
                {
                    "month":
                        month,

                    "total":
                        len(rows),

                    "working":
                        sum(
                            status
                            == "WORKING"
                            for status
                            in statuses
                        ),

                    "processing":
                        sum(
                            status
                            == "PROCESSING"
                            for status
                            in statuses
                        ),

                    "cancelled":
                        sum(
                            status
                            in {
                                "CANCELLED",
                                "TO BE CANCELLED",
                            }
                            for status
                            in statuses
                        ),

                    "released":
                        sum(
                            status
                            == "RELEASED"
                            for status
                            in statuses
                        ),

                    "rejected":
                        sum(
                            status
                            == "REJECTED"
                            for status
                            in statuses
                        ),
                }
            )


        return result