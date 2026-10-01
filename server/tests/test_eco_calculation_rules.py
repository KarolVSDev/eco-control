from datetime import (
    date,
    datetime,
)

from types import (
    SimpleNamespace,
)

import pytest

from app.utils.eco_calculations import (
    OPEN_STATUSES,
    business_days_between,
    compute_eco_fields,
    days_between,
    excel_week_number,
    gap_or_zero,
    normalize_status,
    select_release_date,
    sum_gaps,
    to_date,
    week_label,
)


# =========================================================
# FACTORY
# =========================================================

def calculation_row(
    **overrides,
):
    values = {
        "eco":
            "ECO-TEST",

        "status":
            "WORKING",

        # ECO HQ
        "hq_eco_release_date":
            date(
                2026,
                4,
                1,
            ),

        "az_eco_register_date":
            date(
                2026,
                4,
                3,
            ),

        # ORIGEM
        "hz_sh_in_receive_date_1":
            date(
                2026,
                4,
                5,
            ),

        "hz_sh_in_receive_date_2":
            date(
                2026,
                4,
                7,
            ),

        "hz_sh_in_receive_date_3":
            None,

        # AZ ECO
        "az_eco_creation_date":
            date(
                2026,
                4,
                4,
            ),

        # AGREEMENT
        "agreement_start_1":
            date(
                2026,
                4,
                5,
            ),

        "agreement_finish_1":
            date(
                2026,
                4,
                8,
            ),

        "agreement_start_2":
            date(
                2026,
                4,
                10,
            ),

        "agreement_finish_2":
            date(
                2026,
                4,
                10,
            ),

        "agreement_start_3":
            None,

        "agreement_finish_3":
            None,

        # R&D
        "second_aprov_rd_start_1":
            date(
                2026,
                4,
                12,
            ),

        "second_aprov_rd_finish_1":
            date(
                2026,
                4,
                22,
            ),

        "second_aprov_rd_start_2":
            date(
                2026,
                4,
                23,
            ),

        "second_aprov_rd_finish_2":
            date(
                2026,
                4,
                27,
            ),
    }


    values.update(
        overrides
    )


    return SimpleNamespace(
        **values
    )


# =========================================================
# TO DATE
# =========================================================

@pytest.mark.parametrize(
    (
        "value",
        "expected",
    ),
    [
        (
            date(
                2026,
                4,
                3,
            ),
            date(
                2026,
                4,
                3,
            ),
        ),
        (
            datetime(
                2026,
                4,
                3,
                23,
                59,
            ),
            date(
                2026,
                4,
                3,
            ),
        ),
        (
            "2026-04-03T12:30:00Z",
            date(
                2026,
                4,
                3,
            ),
        ),
        (
            "not-a-date",
            None,
        ),
        (
            None,
            None,
        ),
    ],
)
def test_to_date_supported_inputs(
    value,
    expected,
):
    assert (
        to_date(
            value
        )
        ==
        expected
    )


# =========================================================
# DAYS BETWEEN
# =========================================================

def test_days_between():

    assert (
        days_between(
            date(
                2026,
                4,
                1,
            ),
            date(
                2026,
                4,
                3,
            ),
        )
        == 2
    )


    assert (
        days_between(
            date(
                2026,
                4,
                3,
            ),
            date(
                2026,
                4,
                1,
            ),
        )
        == -2
    )


    assert (
        days_between(
            date(
                2026,
                4,
                1,
            ),
            None,
        )
        is None
    )


# =========================================================
# NORMALIZAÇÃO DE STATUS
# =========================================================

@pytest.mark.parametrize(
    (
        "value",
        "expected",
    ),
    [
        (
            "WORKING",
            "WORKING",
        ),
        (
            " working ",
            "WORKING",
        ),
        (
            "MEC/ HW ANALISYS",
            "MEC/HW ANALISYS",
        ),
        (
            "MEC / HW ANALISYS",
            "MEC/HW ANALISYS",
        ),
        (
            None,
            "",
        ),
    ],
)
def test_normalize_status(
    value,
    expected,
):

    assert (
        normalize_status(
            value
        )
        ==
        expected
    )


# =========================================================
# SEMANA
# =========================================================

def test_excel_week_number():

    assert (
        excel_week_number(
            date(
                2025,
                1,
                1,
            )
        )
        == 1
    )


    assert (
        excel_week_number(
            date(
                2025,
                1,
                6,
            )
        )
        == 2
    )


def test_week_label():

    assert (
        week_label(
            date(
                2025,
                1,
                1,
            )
        )
        ==
        "25 - W01"
    )


    assert (
        week_label(
            date(
                2025,
                1,
                6,
            )
        )
        ==
        "25 - W02"
    )


    assert (
        week_label(
            None
        )
        is None
    )


def test_week_label_year_boundary():

    # Diferente do ISO.
    #
    # 01/01/2021 pertence à primeira
    # semana de 2021 na tabela WEEK.

    assert (
        week_label(
            date(
                2021,
                1,
                1,
            )
        )
        ==
        "21 - W01"
    )


# =========================================================
# NETWORKDAYS
# =========================================================

def test_business_days_between_same_week():

    assert (
        business_days_between(
            date(
                2026,
                1,
                5,
            ),
            date(
                2026,
                1,
                9,
            ),
        )
        == 5
    )


def test_business_days_between_ignores_weekend():

    assert (
        business_days_between(
            date(
                2026,
                1,
                5,
            ),
            date(
                2026,
                1,
                12,
            ),
        )
        == 6
    )


def test_business_days_between_single_weekday():

    assert (
        business_days_between(
            date(
                2026,
                1,
                5,
            ),
            date(
                2026,
                1,
                5,
            ),
        )
        == 1
    )


def test_business_days_between_single_weekend():

    assert (
        business_days_between(
            date(
                2026,
                1,
                10,
            ),
            date(
                2026,
                1,
                10,
            ),
        )
        == 0
    )


def test_business_days_between_reverse():

    assert (
        business_days_between(
            date(
                2026,
                1,
                12,
            ),
            date(
                2026,
                1,
                5,
            ),
        )
        == -6
    )


# =========================================================
# GAP OR ZERO
# =========================================================

def test_gap_or_zero_without_start():

    assert (
        gap_or_zero(
            None,
            None,
        )
        == 0
    )


def test_gap_or_zero_complete_period():

    assert (
        gap_or_zero(
            date(
                2026,
                1,
                1,
            ),
            date(
                2026,
                1,
                5,
            ),
        )
        == 4
    )


def test_gap_or_zero_started_but_not_finished():

    assert (
        gap_or_zero(
            date(
                2026,
                1,
                1,
            ),
            None,
        )
        is None
    )


# =========================================================
# SUM GAPS
# =========================================================

def test_sum_gaps():

    assert (
        sum_gaps(
            [
                3,
                0,
                2,
            ]
        )
        == 5
    )


def test_sum_gaps_with_incomplete_period():

    assert (
        sum_gaps(
            [
                3,
                None,
                2,
            ]
        )
        is None
    )


def test_sum_gaps_all_zero():

    assert (
        sum_gaps(
            [
                0,
                0,
                0,
            ]
        )
        == 0
    )


# =========================================================
# RELEASE DATE
# =========================================================

def test_release_date_prefers_second_finish():

    row = (
        calculation_row(
            second_aprov_rd_finish_1=date(
                2026,
                1,
                10,
            ),

            second_aprov_rd_finish_2=date(
                2026,
                2,
                10,
            ),
        )
    )


    assert (
        select_release_date(
            row
        )
        ==
        date(
            2026,
            2,
            10,
        )
    )


def test_release_date_falls_back_to_first_finish():

    row = (
        calculation_row(
            second_aprov_rd_finish_1=date(
                2026,
                1,
                10,
            ),

            second_aprov_rd_finish_2=None,
        )
    )


    assert (
        select_release_date(
            row
        )
        ==
        date(
            2026,
            1,
            10,
        )
    )


# =========================================================
# CÁLCULOS GERAIS
# =========================================================

def test_calculation_rules_for_date_groups():

    result = (
        compute_eco_fields(
            calculation_row(),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    # GAP
    assert (
        result["gap"]
        == 17
    )


    # ECO HQ
    assert (
        result[
            "delay_eco_register"
        ]
        == 2
    )


    assert (
        result[
            "eco_registration_week"
        ]
        ==
        "26 - W14"
    )


    # ORIGEM
    #
    # Agora parte de HQ ECO RELEASE DATE
    # 01/04.

    assert (
        result[
            "eco_origem_1"
        ]
        == 4
    )


    assert (
        result[
            "eco_origem_2"
        ]
        == 6
    )


    assert (
        result[
            "eco_origem_3"
        ]
        is None
    )


    # AZ ECO
    assert (
        result[
            "gap_start_az_eco"
        ]
        == 1
    )


    # > 1, portanto 1 é False.
    assert (
        result[
            "contar_eco_emitida_1_dias"
        ]
        is False
    )


    # AGREEMENT
    assert (
        result[
            "gap_agreement"
        ]
        is None
    )


    assert (
        result[
            "gap_agreement_1"
        ]
        == 3
    )


    assert (
        result[
            "gap_agreement_2"
        ]
        == 0
    )


    assert (
        result[
            "gap_agreement_3"
        ]
        == 0
    )


    assert (
        result[
            "gap_total_agreement"
        ]
        == 3
    )


    # R&D
    assert (
        result[
            "gap_2st_1"
        ]
        == 10
    )


    assert (
        result[
            "gap_2st_2"
        ]
        == 4
    )


    assert (
        result[
            "gap_total_2st"
        ]
        == 14
    )


    # RELEASE
    #
    # FINISH (2) = 27/04/2026
    assert (
        result[
            "eco_release_week"
        ]
        ==
        "26 - W18"
    )


    # NETWORKDAYS:
    # 03/04 até 27/04.
    assert (
        result[
            "az_gap"
        ]
        == 17
    )


    assert (
        result[
            "contar_eco_7"
        ]
        is True
    )


    assert (
        result[
            "contar_eco_10"
        ]
        is True
    )


    assert (
        result[
            "contar_eco_14"
        ]
        is True
    )


    # TOTAL GAP continua usando FINISH (1).
    assert (
        result[
            "total_gap"
        ]
        == 21
    )


    assert (
        result[
            "release_month"
        ]
        ==
        "ABR"
    )


    assert (
        result[
            "release_year"
        ]
        ==
        "26"
    )


# =========================================================
# GAP TERMINAL
# =========================================================

@pytest.mark.parametrize(
    "status",
    [
        "RELEASED",
        "CANCELLED",
    ],
)
def test_gap_returns_ok_for_terminal_status(
    status,
):

    result = (
        compute_eco_fields(
            calculation_row(
                status=status
            ),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    assert (
        result["gap"]
        ==
        "OK"
    )


# =========================================================
# GAP SEM ECO / DATA
# =========================================================

def test_gap_is_empty_without_eco():

    result = (
        compute_eco_fields(
            calculation_row(
                eco=None
            ),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    assert (
        result["gap"]
        ==
        ""
    )


def test_gap_is_empty_without_register_date():

    result = (
        compute_eco_fields(
            calculation_row(
                az_eco_register_date=None
            ),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    assert (
        result["gap"]
        ==
        ""
    )


# =========================================================
# GAP AGREEMENT
# =========================================================

@pytest.mark.parametrize(
    "status",
    OPEN_STATUSES,
)
def test_gap_agreement_is_not_calculated_for_open_statuses(
    status,
):

    result = (
        compute_eco_fields(
            calculation_row(
                status=status
            ),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    assert (
        result[
            "gap_agreement"
        ]
        is None
    )


def test_gap_agreement_accepts_spaced_status():

    result = (
        compute_eco_fields(
            calculation_row(
                status=(
                    "MEC/ HW ANALISYS"
                )
            ),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    assert (
        result[
            "gap_agreement"
        ]
        is None
    )


def test_gap_agreement_uses_today_for_closed_status():

    result = (
        compute_eco_fields(
            calculation_row(
                status="DONE"
            ),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    assert (
        result[
            "gap_agreement"
        ]
        == 15
    )


# =========================================================
# PERÍODOS INCOMPLETOS
# =========================================================

def test_agreement_started_without_finish_is_none():

    result = (
        compute_eco_fields(
            calculation_row(
                agreement_start_1=date(
                    2026,
                    4,
                    5,
                ),

                agreement_finish_1=None,

                agreement_start_2=None,
                agreement_finish_2=None,

                agreement_start_3=None,
                agreement_finish_3=None,
            )
        )
    )


    assert (
        result[
            "gap_agreement_1"
        ]
        is None
    )


    assert (
        result[
            "gap_total_agreement"
        ]
        is None
    )


def test_rd_started_without_finish_is_none():

    result = (
        compute_eco_fields(
            calculation_row(
                second_aprov_rd_start_1=date(
                    2026,
                    4,
                    5,
                ),

                second_aprov_rd_finish_1=None,

                second_aprov_rd_start_2=None,
                second_aprov_rd_finish_2=None,
            )
        )
    )


    assert (
        result[
            "gap_2st_1"
        ]
        is None
    )


    assert (
        result[
            "gap_total_2st"
        ]
        is None
    )


# =========================================================
# CAMPOS SEM DATAS
# =========================================================

def test_missing_dates():

    result = (
        compute_eco_fields(
            calculation_row(
                hq_eco_release_date=None,

                az_eco_register_date=None,

                az_eco_creation_date=None,

                hz_sh_in_receive_date_1=None,

                hz_sh_in_receive_date_2=None,

                hz_sh_in_receive_date_3=None,

                agreement_start_1=None,

                agreement_finish_1=None,

                agreement_start_2=None,

                agreement_finish_2=None,

                agreement_start_3=None,

                agreement_finish_3=None,

                second_aprov_rd_start_1=None,

                second_aprov_rd_finish_1=None,

                second_aprov_rd_start_2=None,

                second_aprov_rd_finish_2=None,
            ),
            today=date(
                2026,
                4,
                20,
            ),
        )
    )


    assert (
        result[
            "delay_eco_register"
        ]
        is None
    )


    assert (
        result[
            "eco_registration_week"
        ]
        is None
    )


    assert (
        result[
            "eco_origem_1"
        ]
        is None
    )


    assert (
        result[
            "eco_origem_2"
        ]
        is None
    )


    assert (
        result[
            "eco_origem_3"
        ]
        is None
    )


    assert (
        result[
            "gap_total_agreement"
        ]
        == 0
    )


    assert (
        result[
            "gap_total_2st"
        ]
        == 0
    )


    assert (
        result[
            "eco_release_week"
        ]
        ==
        "-"
    )


    assert (
        result[
            "az_gap"
        ]
        is None
    )


    assert (
        result[
            "contar_eco_7"
        ]
        is False
    )


    assert (
        result[
            "contar_eco_10"
        ]
        is False
    )


    assert (
        result[
            "contar_eco_14"
        ]
        is False
    )


    assert (
        result[
            "release_month"
        ]
        ==
        "-"
    )


    assert (
        result[
            "release_year"
        ]
        ==
        "-"
    )