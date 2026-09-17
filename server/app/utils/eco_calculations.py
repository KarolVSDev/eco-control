from datetime import date, datetime


MONTH_ABBR = [
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


# Mantido exatamente conforme a regra existente
# no ecoCalc.js exportado do Base44.
OPEN_STATUSES = [
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
]


def to_date(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(
                value[:10]
            )
        except ValueError:
            return None

    return None


def days_between(start, end):
    start_date = to_date(start)
    end_date = to_date(end)

    if not start_date or not end_date:
        return None

    return (
        end_date - start_date
    ).days


def week_label(value):
    parsed = to_date(value)

    if not parsed:
        return None

    iso_week = parsed.isocalendar().week
    year = str(parsed.year)[-2:]

    return f"{year}-W{iso_week:02d}"


def sum_ignoring_none(values):
    valid = [
        value
        for value in values
        if value is not None
    ]

    if not valid:
        return None

    return sum(valid)


def compute_eco_fields(row):
    # -------------------------------------------------
    # GAP
    # -------------------------------------------------
    if not row.eco:
        gap = ""

    elif row.status in {
        "RELEASED",
        "CANCELLED",
    }:
        gap = "OK"

    elif row.az_eco_register_date:
        gap = days_between(
            row.az_eco_register_date,
            date.today(),
        )

    else:
        gap = ""

    # -------------------------------------------------
    # ECO HQ
    # -------------------------------------------------
    delay_eco_register = days_between(
        row.hq_eco_release_date,
        row.az_eco_register_date,
    )

    eco_registration_week = week_label(
        row.az_eco_register_date
    )

    # -------------------------------------------------
    # ORIGEM
    # -------------------------------------------------
    eco_origem_1 = days_between(
        row.az_eco_register_date,
        row.hz_sh_in_receive_date_1,
    )

    eco_origem_2 = days_between(
        row.az_eco_register_date,
        row.hz_sh_in_receive_date_2,
    )

    eco_origem_3 = days_between(
        row.az_eco_register_date,
        row.hz_sh_in_receive_date_3,
    )

    # -------------------------------------------------
    # AZ ECO
    # -------------------------------------------------
    gap_start_az_eco = days_between(
        row.az_eco_register_date,
        row.az_eco_creation_date,
    )

    contar_eco_emitida_1_dias = (
        gap_start_az_eco >= 1
        if gap_start_az_eco is not None
        else None
    )

    gap_agreement = None

    if (
        row.eco
        and row.status not in OPEN_STATUSES
        and row.agreement_start_1
    ):
        gap_agreement = days_between(
            row.agreement_start_1,
            date.today(),
        )

    # -------------------------------------------------
    # AGREEMENT OTHER DEPTS
    # -------------------------------------------------
    gap_agreement_1 = days_between(
        row.agreement_start_1,
        row.agreement_finish_1,
    )

    gap_agreement_2 = days_between(
        row.agreement_start_2,
        row.agreement_finish_2,
    )

    gap_agreement_3 = days_between(
        row.agreement_start_3,
        row.agreement_finish_3,
    )

    gap_total_agreement = sum_ignoring_none(
        [
            gap_agreement_1,
            gap_agreement_2,
            gap_agreement_3,
        ]
    )

    # -------------------------------------------------
    # R&D APPROVAL
    # -------------------------------------------------
    gap_2st_1 = days_between(
        row.second_aprov_rd_start_1,
        row.second_aprov_rd_finish_1,
    )

    gap_2st_2 = days_between(
        row.second_aprov_rd_start_2,
        row.second_aprov_rd_finish_2,
    )

    gap_total_2st = sum_ignoring_none(
        [
            gap_2st_1,
            gap_2st_2,
        ]
    )

    # -------------------------------------------------
    # RELEASE
    # -------------------------------------------------
    release_date = to_date(
        row.second_aprov_rd_finish_1
    )

    eco_release_week = (
        week_label(release_date)
        if release_date
        else "-"
    )

    az_gap = days_between(
        row.az_eco_creation_date,
        row.second_aprov_rd_finish_1,
    )

    contar_eco_7 = (
        az_gap > 7
        if az_gap is not None
        else None
    )

    contar_eco_10 = (
        az_gap > 10
        if az_gap is not None
        else None
    )

    # Mantido para Dashboard / regra GAP > 14.
    # Não será exibido como coluna principal.
    contar_eco_14 = (
        az_gap > 14
        if az_gap is not None
        else None
    )

    total_gap = days_between(
        row.hq_eco_release_date,
        row.second_aprov_rd_finish_1,
    )

    release_month = (
        MONTH_ABBR[
            release_date.month - 1
        ]
        if release_date
        else "-"
    )

    release_year = (
        str(release_date.year)[-2:]
        if release_date
        else "-"
    )

    return {
        "gap": gap,
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


def normalize_text(value):
    if isinstance(value, str):
        return value.strip()

    return value