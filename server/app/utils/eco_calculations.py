from datetime import (
    date,
    datetime,
    timedelta,
)


# =========================================================
# MESES
#
# A planilha CTRL GERAL utiliza abreviações em português.
# =========================================================

MONTH_ABBR = [
    "JAN",
    "FEV",
    "MAR",
    "ABR",
    "MAI",
    "JUN",
    "JUL",
    "AGO",
    "SET",
    "OUT",
    "NOV",
    "DEZ",
]


# =========================================================
# STATUS QUE NÃO DEVEM GERAR GAP AGREEMENT
#
# A planilha possui "MEC/ HW ANALISYS".
# O sistema já utiliza "MEC/HW ANALISYS".
#
# normalize_status() transforma ambos na mesma forma.
# =========================================================

OPEN_STATUSES = {
    "WORKING",
    "ON HOLD",
    "WAITING HZ/IN/ND",
    "MEC/HW ANALISYS",
    "COUNCIL MEETING",
    "SPOC ON APPROVAL",
    "WAITING NEW ECO TO FIX BOM",
    "REJECTED",
    "RELEASED",
    "TO BE CANCELLED",
    "CANCELLED",
}


# =========================================================
# NORMALIZAÇÃO DE STATUS
# =========================================================

def normalize_status(value):
    if value is None:
        return ""

    normalized = " ".join(
        str(value)
        .strip()
        .upper()
        .split()
    )

    return (
        normalized
        .replace(
            "/ ",
            "/",
        )
        .replace(
            " /",
            "/",
        )
    )


# =========================================================
# CONVERSÃO PARA DATA
# =========================================================

def to_date(value):
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    if isinstance(
        value,
        date,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        try:
            return date.fromisoformat(
                value[:10]
            )

        except ValueError:
            return None

    return None


# =========================================================
# DIFERENÇA EM DIAS CORRIDOS
# =========================================================

def days_between(
    start,
    end,
):
    start_date = to_date(
        start
    )

    end_date = to_date(
        end
    )

    if (
        not start_date
        or
        not end_date
    ):
        return None

    return (
        end_date
        - start_date
    ).days


# =========================================================
# NETWORKDAYS DO EXCEL
# =========================================================

def business_days_between(
    start,
    end,
):
    """
    Equivalente ao NETWORKDAYS do Excel,
    sem lista adicional de feriados.

    Conta somente segunda a sexta.

    As datas inicial e final são incluídas
    quando forem dias úteis.
    """

    start_date = to_date(
        start
    )

    end_date = to_date(
        end
    )

    if (
        not start_date
        or
        not end_date
    ):
        return None


    sign = 1


    if (
        start_date
        > end_date
    ):
        start_date, end_date = (
            end_date,
            start_date,
        )

        sign = -1


    total_days = (
        end_date
        - start_date
    ).days + 1


    full_weeks, remainder = (
        divmod(
            total_days,
            7,
        )
    )


    total = (
        full_weeks
        * 5
    )


    remainder_start = (
        start_date
        +
        timedelta(
            days=(
                full_weeks
                * 7
            )
        )
    )


    for offset in range(
        remainder
    ):
        current = (
            remainder_start
            +
            timedelta(
                days=offset
            )
        )


        if (
            current.weekday()
            < 5
        ):
            total += 1


    return (
        total
        * sign
    )


# =========================================================
# SEMANA DA PLANILHA
# =========================================================

def excel_week_number(
    value,
):
    """
    Reproduz a tabela WEEK da planilha.

    É equivalente ao comportamento de
    WEEKNUM(data, 2):

    - semana começa na segunda-feira;
    - semana 1 contém 1º de janeiro;
    - o ano não muda para o ano ISO.

    Exemplos da própria tabela:

    30/12/2024 -> W53
    01/01/2025 -> W01
    06/01/2025 -> W02
    """

    parsed = to_date(
        value
    )


    if not parsed:
        return None


    first_day = date(
        parsed.year,
        1,
        1,
    )


    return (
        (
            (
                parsed
                - first_day
            ).days
            +
            first_day.weekday()
        )
        // 7
    ) + 1


def week_label(
    value,
):
    parsed = to_date(
        value
    )


    if not parsed:
        return None


    week = (
        excel_week_number(
            parsed
        )
    )


    year = str(
        parsed.year
    )[-2:]


    return (
        f"{year} - W{week:02d}"
    )


# =========================================================
# GAP DE PERÍODOS
# =========================================================

def gap_or_zero(
    start,
    end,
):
    """
    A planilha retorna 0 quando não existe
    uma data inicial para o período.

    Quando existe início, mas não existe fim,
    não reproduzimos o número negativo gerado
    pelo Excel.

    Nesse caso retornamos None para que o
    futuro upload possa sinalizar a linha
    como incompleta.
    """

    start_date = to_date(
        start
    )

    end_date = to_date(
        end
    )


    if not start_date:
        return 0


    if not end_date:
        return None


    return (
        end_date
        - start_date
    ).days


def sum_gaps(
    values,
):
    """
    Se algum período foi iniciado mas
    não foi finalizado, o total também
    permanece indefinido.

    Caso contrário, soma normalmente.

    Exemplo:
    [0, 0, 0] -> 0
    [3, 0, 0] -> 3
    [3, None, 0] -> None
    """

    if any(
        value is None
        for value
        in values
    ):
        return None


    return sum(
        values
    )


# =========================================================
# DATA FINAL DE RELEASE
# =========================================================

def select_release_date(
    row,
):
    """
    Regra utilizada pelos campos de release
    da CTRL GERAL:

    se existir R&D FINISH (2),
    utilizar FINISH (2);

    caso contrário,
    utilizar FINISH (1).
    """

    second_finish = to_date(
        getattr(
            row,
            "second_aprov_rd_finish_2",
            None,
        )
    )


    if second_finish:
        return second_finish


    return to_date(
        getattr(
            row,
            "second_aprov_rd_finish_1",
            None,
        )
    )


# =========================================================
# CÁLCULOS DA ECO
# =========================================================

def compute_eco_fields(
    row,
    *,
    today: date | None = None,
):
    reference_date = (
        today
        or
        date.today()
    )


    status = (
        normalize_status(
            getattr(
                row,
                "status",
                None,
            )
        )
    )


    # =====================================================
    # GAP
    #
    # Excel:
    #
    # IF(
    #   ECO="",
    #   "",
    #   IF(
    #       STATUS RELEASED/CANCELLED,
    #       "OK",
    #       TODAY() - AZ ECO REGISTER DATE
    #   )
    # )
    # =====================================================

    if not getattr(
        row,
        "eco",
        None,
    ):
        gap = ""


    elif (
        status
        in {
            "RELEASED",
            "CANCELLED",
        }
    ):
        gap = "OK"


    elif to_date(
        getattr(
            row,
            "az_eco_register_date",
            None,
        )
    ):
        gap = days_between(
            getattr(
                row,
                "az_eco_register_date",
                None,
            ),
            reference_date,
        )


    else:
        gap = ""


    # =====================================================
    # ECO HQ
    # =====================================================

    delay_eco_register = (
        days_between(
            getattr(
                row,
                "hq_eco_release_date",
                None,
            ),
            getattr(
                row,
                "az_eco_register_date",
                None,
            ),
        )
    )


    eco_registration_week = (
        week_label(
            getattr(
                row,
                "az_eco_register_date",
                None,
            )
        )
    )


    # =====================================================
    # ORIGEM
    #
    # CTRL GERAL:
    #
    # RECEIVE DATE
    # -
    # HQ ECO RELEASE DATE
    #
    # O backend antigo utilizava
    # AZ ECO REGISTER DATE como início.
    # =====================================================

    eco_origem_1 = (
        days_between(
            getattr(
                row,
                "hq_eco_release_date",
                None,
            ),
            getattr(
                row,
                "hz_sh_in_receive_date_1",
                None,
            ),
        )
    )


    eco_origem_2 = (
        days_between(
            getattr(
                row,
                "hq_eco_release_date",
                None,
            ),
            getattr(
                row,
                "hz_sh_in_receive_date_2",
                None,
            ),
        )
    )


    eco_origem_3 = (
        days_between(
            getattr(
                row,
                "hq_eco_release_date",
                None,
            ),
            getattr(
                row,
                "hz_sh_in_receive_date_3",
                None,
            ),
        )
    )


    # =====================================================
    # AZ ECO
    # =====================================================

    gap_start_az_eco = (
        days_between(
            getattr(
                row,
                "az_eco_register_date",
                None,
            ),
            getattr(
                row,
                "az_eco_creation_date",
                None,
            ),
        )
    )


    # Excel:
    # IF(AI > 1, TRUE, FALSE)
    #
    # Portanto:
    # 1 dia  -> FALSE
    # 2 dias -> TRUE

    contar_eco_emitida_1_dias = (
        gap_start_az_eco > 1
        if (
            gap_start_az_eco
            is not None
        )
        else False
    )


    # =====================================================
    # GAP AGREEMENT
    # =====================================================

    gap_agreement = None


    agreement_start_1 = (
        getattr(
            row,
            "agreement_start_1",
            None,
        )
    )


    if (
        getattr(
            row,
            "eco",
            None,
        )
        and
        status
        not in OPEN_STATUSES
        and
        to_date(
            agreement_start_1
        )
    ):
        gap_agreement = (
            days_between(
                agreement_start_1,
                reference_date,
            )
        )


    # =====================================================
    # AGREEMENT OTHER DEPTS
    # =====================================================

    gap_agreement_1 = (
        gap_or_zero(
            getattr(
                row,
                "agreement_start_1",
                None,
            ),
            getattr(
                row,
                "agreement_finish_1",
                None,
            ),
        )
    )


    gap_agreement_2 = (
        gap_or_zero(
            getattr(
                row,
                "agreement_start_2",
                None,
            ),
            getattr(
                row,
                "agreement_finish_2",
                None,
            ),
        )
    )


    gap_agreement_3 = (
        gap_or_zero(
            getattr(
                row,
                "agreement_start_3",
                None,
            ),
            getattr(
                row,
                "agreement_finish_3",
                None,
            ),
        )
    )


    gap_total_agreement = (
        sum_gaps(
            [
                gap_agreement_1,
                gap_agreement_2,
                gap_agreement_3,
            ]
        )
    )


    # =====================================================
    # R&D APPROVAL
    # =====================================================

    gap_2st_1 = (
        gap_or_zero(
            getattr(
                row,
                "second_aprov_rd_start_1",
                None,
            ),
            getattr(
                row,
                "second_aprov_rd_finish_1",
                None,
            ),
        )
    )


    gap_2st_2 = (
        gap_or_zero(
            getattr(
                row,
                "second_aprov_rd_start_2",
                None,
            ),
            getattr(
                row,
                "second_aprov_rd_finish_2",
                None,
            ),
        )
    )


    gap_total_2st = (
        sum_gaps(
            [
                gap_2st_1,
                gap_2st_2,
            ]
        )
    )


    # =====================================================
    # RELEASE
    # =====================================================

    release_date = (
        select_release_date(
            row
        )
    )


    eco_release_week = (
        week_label(
            release_date
        )
        if release_date
        else "-"
    )


    # =====================================================
    # AZ GAP
    #
    # A CTRL GERAL utiliza NETWORKDAYS.
    #
    # A fórmula do Excel possui uma inconsistência
    # na seleção entre FINISH (1) e FINISH (2).
    #
    # Para o sistema usamos a mesma data de release:
    #
    # FINISH (2), quando existir;
    # senão FINISH (1).
    # =====================================================

    az_gap = (
        business_days_between(
            getattr(
                row,
                "az_eco_register_date",
                None,
            ),
            release_date,
        )
    )


    # =====================================================
    # CONTADORES
    # =====================================================

    contar_eco_7 = (
        az_gap > 7
        if (
            az_gap
            is not None
        )
        else False
    )


    contar_eco_10 = (
        az_gap > 10
        if (
            az_gap
            is not None
        )
        else False
    )


    # Mantido para Dashboard.
    contar_eco_14 = (
        az_gap > 14
        if (
            az_gap
            is not None
        )
        else False
    )


    # =====================================================
    # TOTAL GAP
    #
    # A fórmula da planilha usa apenas FINISH (1):
    #
    # R&D FINISH (1)
    # -
    # HQ ECO RELEASE DATE
    # =====================================================

    total_gap = (
        days_between(
            getattr(
                row,
                "hq_eco_release_date",
                None,
            ),
            getattr(
                row,
                "second_aprov_rd_finish_1",
                None,
            ),
        )
    )


    # =====================================================
    # RELEASE MONTH
    # =====================================================

    release_month = (
        MONTH_ABBR[
            release_date.month
            - 1
        ]
        if release_date
        else "-"
    )


    # =====================================================
    # RELEASE YEAR
    #
    # A fórmula "aaa" existente na planilha produz
    # "AAA" em algumas células.
    #
    # Isso é um defeito da fórmula/locale da planilha.
    #
    # Mantemos a intenção utilizada pelo sistema:
    # ano com dois dígitos.
    # =====================================================

    release_year = (
        str(
            release_date.year
        )[-2:]
        if release_date
        else "-"
    )


    # =====================================================
    # RESULTADO
    # =====================================================

    return {
        "gap":
            gap,

        "delay_eco_register":
            delay_eco_register,

        "eco_registration_week":
            eco_registration_week,

        "eco_origem_1":
            eco_origem_1,

        "eco_origem_2":
            eco_origem_2,

        "eco_origem_3":
            eco_origem_3,

        "gap_start_az_eco":
            gap_start_az_eco,

        "contar_eco_emitida_1_dias":
            contar_eco_emitida_1_dias,

        "gap_agreement":
            gap_agreement,

        "gap_agreement_1":
            gap_agreement_1,

        "gap_agreement_2":
            gap_agreement_2,

        "gap_agreement_3":
            gap_agreement_3,

        "gap_total_agreement":
            gap_total_agreement,

        "gap_2st_1":
            gap_2st_1,

        "gap_2st_2":
            gap_2st_2,

        "gap_total_2st":
            gap_total_2st,

        "eco_release_week":
            eco_release_week,

        "az_gap":
            az_gap,

        "contar_eco_7":
            contar_eco_7,

        "contar_eco_10":
            contar_eco_10,

        "contar_eco_14":
            contar_eco_14,

        "total_gap":
            total_gap,

        "release_month":
            release_month,

        "release_year":
            release_year,
    }


# =========================================================
# NORMALIZAÇÃO DE TEXTO
# =========================================================

def normalize_text(
    value,
):
    if isinstance(
        value,
        str,
    ):
        return value.strip()

    return value