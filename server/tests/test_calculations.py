from datetime import date
from types import SimpleNamespace

from app.utils.eco_calculations import (
    business_days_between,
    compute_eco_fields,
    week_label,
)


# =========================================================
# HELPERS
# =========================================================

def make_row(
    **overrides,
):
    """
    Cria uma ECO mínima para testar
    os cálculos do backend.

    Todos os campos utilizados por
    compute_eco_fields ficam disponíveis,
    mas podem ser sobrescritos em cada teste.
    """

    attrs = {
        "eco":
            "TESTE-001",

        "status":
            "WORKING",

        # ECO HQ
        "hq_eco_release_date":
            None,

        "az_eco_register_date":
            None,

        # ORIGEM
        "hz_sh_in_receive_date_1":
            None,

        "hz_sh_in_receive_date_2":
            None,

        "hz_sh_in_receive_date_3":
            None,

        # AZ ECO
        "az_eco_creation_date":
            None,

        # AGREEMENT
        "agreement_start_1":
            None,

        "agreement_finish_1":
            None,

        "agreement_start_2":
            None,

        "agreement_finish_2":
            None,

        "agreement_start_3":
            None,

        "agreement_finish_3":
            None,

        # R&D
        "second_aprov_rd_start_1":
            None,

        "second_aprov_rd_finish_1":
            None,

        "second_aprov_rd_start_2":
            None,

        "second_aprov_rd_finish_2":
            None,
    }


    attrs.update(
        overrides
    )


    return SimpleNamespace(
        **attrs
    )


# =========================================================
# GAP PRINCIPAL
# =========================================================

def test_gap_without_eco_is_empty():

    calculated = (
        compute_eco_fields(
            make_row(
                eco=None,
                az_eco_register_date=date(
                    2026,
                    1,
                    1,
                ),
            ),
            today=date(
                2026,
                1,
                10,
            ),
        )
    )


    assert (
        calculated["gap"]
        == ""
    )


def test_gap_released_is_ok():

    calculated = (
        compute_eco_fields(
            make_row(
                status="RELEASED",
                az_eco_register_date=date(
                    2026,
                    1,
                    1,
                ),
            ),
            today=date(
                2026,
                1,
                10,
            ),
        )
    )


    assert (
        calculated["gap"]
        == "OK"
    )


def test_gap_cancelled_is_ok():

    calculated = (
        compute_eco_fields(
            make_row(
                status="CANCELLED",
                az_eco_register_date=date(
                    2026,
                    1,
                    1,
                ),
            ),
            today=date(
                2026,
                1,
                10,
            ),
        )
    )


    assert (
        calculated["gap"]
        == "OK"
    )


def test_gap_working_counts_calendar_days():

    calculated = (
        compute_eco_fields(
            make_row(
                status="WORKING",
                az_eco_register_date=date(
                    2026,
                    1,
                    1,
                ),
            ),
            today=date(
                2026,
                1,
                10,
            ),
        )
    )


    assert (
        calculated["gap"]
        == 9
    )


# =========================================================
# DELAY ECO REGISTER
# =========================================================

def test_delay_eco_register():

    calculated = (
        compute_eco_fields(
            make_row(
                hq_eco_release_date=date(
                    2026,
                    1,
                    1,
                ),

                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),
            )
        )
    )


    assert (
        calculated[
            "delay_eco_register"
        ]
        == 4
    )


# =========================================================
# SEMANAS
# =========================================================

def test_week_label_first_week():

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


def test_week_label_second_week():

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


def test_week_label_end_of_year():

    assert (
        week_label(
            date(
                2024,
                12,
                30,
            )
        )
        ==
        "24 - W53"
    )


def test_eco_registration_week():

    calculated = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2025,
                    1,
                    6,
                ),
            )
        )
    )


    assert (
        calculated[
            "eco_registration_week"
        ]
        ==
        "25 - W02"
    )


# =========================================================
# ECO ORIGEM
# =========================================================

def test_eco_origem_uses_hq_release_date():

    calculated = (
        compute_eco_fields(
            make_row(
                hq_eco_release_date=date(
                    2026,
                    1,
                    1,
                ),

                # propositalmente diferente:
                # o cálculo NÃO deve partir daqui
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                hz_sh_in_receive_date_1=date(
                    2026,
                    1,
                    10,
                ),

                hz_sh_in_receive_date_2=date(
                    2026,
                    1,
                    15,
                ),

                hz_sh_in_receive_date_3=date(
                    2026,
                    1,
                    20,
                ),
            )
        )
    )


    assert (
        calculated[
            "eco_origem_1"
        ]
        == 9
    )


    assert (
        calculated[
            "eco_origem_2"
        ]
        == 14
    )


    assert (
        calculated[
            "eco_origem_3"
        ]
        == 19
    )


# =========================================================
# GAP START AZ ECO
# =========================================================

def test_gap_start_az_eco():

    calculated = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    1,
                ),

                az_eco_creation_date=date(
                    2026,
                    1,
                    4,
                ),
            )
        )
    )


    assert (
        calculated[
            "gap_start_az_eco"
        ]
        == 3
    )


# =========================================================
# CONTAR ECO EMITIDA > 1 DIA
# =========================================================

def test_contar_eco_emitida_one_day_is_false():

    calculated = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    1,
                ),

                az_eco_creation_date=date(
                    2026,
                    1,
                    2,
                ),
            )
        )
    )


    assert (
        calculated[
            "contar_eco_emitida_1_dias"
        ]
        is False
    )


def test_contar_eco_emitida_two_days_is_true():

    calculated = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    1,
                ),

                az_eco_creation_date=date(
                    2026,
                    1,
                    3,
                ),
            )
        )
    )


    assert (
        calculated[
            "contar_eco_emitida_1_dias"
        ]
        is True
    )


# =========================================================
# AGREEMENT
# =========================================================

def test_agreement_gaps_and_total():

    calculated = (
        compute_eco_fields(
            make_row(
                agreement_start_1=date(
                    2026,
                    1,
                    1,
                ),

                agreement_finish_1=date(
                    2026,
                    1,
                    4,
                ),

                agreement_start_2=date(
                    2026,
                    1,
                    10,
                ),

                agreement_finish_2=date(
                    2026,
                    1,
                    15,
                ),

                # período 3 não iniciado
                agreement_start_3=None,
                agreement_finish_3=None,
            )
        )
    )


    assert (
        calculated[
            "gap_agreement_1"
        ]
        == 3
    )


    assert (
        calculated[
            "gap_agreement_2"
        ]
        == 5
    )


    assert (
        calculated[
            "gap_agreement_3"
        ]
        == 0
    )


    assert (
        calculated[
            "gap_total_agreement"
        ]
        == 8
    )


def test_incomplete_agreement_returns_none():

    calculated = (
        compute_eco_fields(
            make_row(
                agreement_start_1=date(
                    2026,
                    1,
                    1,
                ),

                agreement_finish_1=None,
            )
        )
    )


    assert (
        calculated[
            "gap_agreement_1"
        ]
        is None
    )


    assert (
        calculated[
            "gap_total_agreement"
        ]
        is None
    )


# =========================================================
# R&D APPROVAL
# =========================================================

def test_rd_gaps_and_total():

    calculated = (
        compute_eco_fields(
            make_row(
                second_aprov_rd_start_1=date(
                    2026,
                    1,
                    1,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_start_2=date(
                    2026,
                    1,
                    10,
                ),

                second_aprov_rd_finish_2=date(
                    2026,
                    1,
                    12,
                ),
            )
        )
    )


    assert (
        calculated[
            "gap_2st_1"
        ]
        == 4
    )


    assert (
        calculated[
            "gap_2st_2"
        ]
        == 2
    )


    assert (
        calculated[
            "gap_total_2st"
        ]
        == 6
    )


def test_rd_second_period_not_started_is_zero():

    calculated = (
        compute_eco_fields(
            make_row(
                second_aprov_rd_start_1=date(
                    2026,
                    1,
                    1,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_start_2=None,
                second_aprov_rd_finish_2=None,
            )
        )
    )


    assert (
        calculated[
            "gap_2st_2"
        ]
        == 0
    )


    assert (
        calculated[
            "gap_total_2st"
        ]
        == 4
    )


# =========================================================
# NETWORKDAYS
# =========================================================

def test_business_days_same_week():

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


def test_business_days_ignores_weekend():

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


# =========================================================
# RELEASE DATE
#
# FINISH (2) tem prioridade quando existe.
# =========================================================

def test_release_uses_second_finish_when_present():

    calculated = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    20,
                ),

                second_aprov_rd_finish_2=date(
                    2026,
                    2,
                    3,
                ),
            )
        )
    )


    assert (
        calculated[
            "eco_release_week"
        ]
        ==
        "26 - W06"
    )


    assert (
        calculated[
            "release_month"
        ]
        ==
        "FEV"
    )


    assert (
        calculated[
            "release_year"
        ]
        ==
        "26"
    )


# =========================================================
# RELEASE FALLBACK
#
# Sem FINISH (2), utiliza FINISH (1).
# =========================================================

def test_release_falls_back_to_first_finish():

    calculated = (
        compute_eco_fields(
            make_row(
                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    20,
                ),

                second_aprov_rd_finish_2=None,
            )
        )
    )


    assert (
        calculated[
            "release_month"
        ]
        ==
        "JAN"
    )


    assert (
        calculated[
            "release_year"
        ]
        ==
        "26"
    )


# =========================================================
# TOTAL GAP
#
# Continua usando FINISH (1),
# conforme a fórmula da CTRL GERAL.
# =========================================================

def test_total_gap_uses_first_finish():

    calculated = (
        compute_eco_fields(
            make_row(
                hq_eco_release_date=date(
                    2026,
                    1,
                    1,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    20,
                ),

                # deve ser ignorado pelo Total Gap
                second_aprov_rd_finish_2=date(
                    2026,
                    2,
                    3,
                ),
            )
        )
    )


    assert (
        calculated[
            "total_gap"
        ]
        == 19
    )


# =========================================================
# AZ GAP
#
# NETWORKDAYS:
# AZ ECO REGISTER DATE
# até a data final de release.
# =========================================================

def test_az_gap_uses_business_days():

    calculated = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    12,
                ),
            )
        )
    )


    # 05, 06, 07, 08, 09 e 12
    assert (
        calculated[
            "az_gap"
        ]
        == 6
    )


# =========================================================
# LIMITE > 7
# =========================================================

def test_gap_7_boundary():

    # 05/01 até 13/01 = 7 dias úteis

    calculated_7 = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    13,
                ),
            )
        )
    )


    # 05/01 até 14/01 = 8 dias úteis

    calculated_8 = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    14,
                ),
            )
        )
    )


    assert (
        calculated_7[
            "contar_eco_7"
        ]
        is False
    )


    assert (
        calculated_8[
            "contar_eco_7"
        ]
        is True
    )


# =========================================================
# LIMITE > 10
# =========================================================

def test_gap_10_boundary():

    # 05/01 até 16/01 = 10 dias úteis

    calculated_10 = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    16,
                ),
            )
        )
    )


    # 05/01 até 19/01 = 11 dias úteis

    calculated_11 = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    19,
                ),
            )
        )
    )


    assert (
        calculated_10[
            "contar_eco_10"
        ]
        is False
    )


    assert (
        calculated_11[
            "contar_eco_10"
        ]
        is True
    )


# =========================================================
# LIMITE > 14
# =========================================================

def test_gap_14_boundary():

    # 05/01 até 22/01 = 14 dias úteis

    calculated_14 = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    22,
                ),
            )
        )
    )


    # 05/01 até 23/01 = 15 dias úteis

    calculated_15 = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=date(
                    2026,
                    1,
                    23,
                ),
            )
        )
    )


    assert (
        calculated_14[
            "az_gap"
        ]
        == 14
    )


    assert (
        calculated_14[
            "contar_eco_14"
        ]
        is False
    )


    assert (
        calculated_15[
            "az_gap"
        ]
        == 15
    )


    assert (
        calculated_15[
            "contar_eco_14"
        ]
        is True
    )


# =========================================================
# SEM DATA DE RELEASE
# =========================================================

def test_without_release_date():

    calculated = (
        compute_eco_fields(
            make_row(
                az_eco_register_date=date(
                    2026,
                    1,
                    5,
                ),

                second_aprov_rd_finish_1=None,

                second_aprov_rd_finish_2=None,
            )
        )
    )


    assert (
        calculated[
            "eco_release_week"
        ]
        == "-"
    )


    assert (
        calculated[
            "az_gap"
        ]
        is None
    )


    assert (
        calculated[
            "contar_eco_7"
        ]
        is False
    )


    assert (
        calculated[
            "contar_eco_10"
        ]
        is False
    )


    assert (
        calculated[
            "contar_eco_14"
        ]
        is False
    )


    assert (
        calculated[
            "release_month"
        ]
        == "-"
    )


    assert (
        calculated[
            "release_year"
        ]
        == "-"
    )