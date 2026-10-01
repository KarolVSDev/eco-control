from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.utils.eco_calculations import (
    OPEN_STATUSES,
    compute_eco_fields,
    days_between,
    sum_ignoring_none,
    to_date,
    week_label,
)


def calculation_row(**overrides):
    values = {
        "eco": "ECO-TEST",
        "status": "WORKING",
        "hq_eco_release_date": date(2026, 4, 1),
        "az_eco_register_date": date(2026, 4, 3),
        "az_eco_creation_date": date(2026, 4, 4),
        "hz_sh_in_receive_date_1": date(2026, 4, 5),
        "hz_sh_in_receive_date_2": date(2026, 4, 7),
        "hz_sh_in_receive_date_3": None,
        "agreement_start_1": date(2026, 4, 5),
        "agreement_finish_1": date(2026, 4, 8),
        "agreement_start_2": date(2026, 4, 10),
        "agreement_finish_2": date(2026, 4, 10),
        "agreement_start_3": None,
        "agreement_finish_3": None,
        "second_aprov_rd_start_1": date(2026, 4, 12),
        "second_aprov_rd_finish_1": date(2026, 4, 22),
        "second_aprov_rd_start_2": date(2026, 4, 23),
        "second_aprov_rd_finish_2": date(2026, 4, 27),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (date(2026, 4, 3), date(2026, 4, 3)),
        (datetime(2026, 4, 3, 23, 59), date(2026, 4, 3)),
        ("2026-04-03T12:30:00Z", date(2026, 4, 3)),
        ("not-a-date", None),
        (None, None),
    ],
)
def test_to_date_supported_inputs(value, expected):
    assert to_date(value) == expected


def test_days_between_is_end_minus_start_and_accepts_negative_result():
    assert days_between(date(2026, 4, 1), date(2026, 4, 3)) == 2
    assert days_between(date(2026, 4, 3), date(2026, 4, 1)) == -2
    assert days_between(date(2026, 4, 1), None) is None


def test_week_label_uses_iso_week_number_for_regular_date():
    assert week_label(date(2026, 4, 3)) == "26-W14"
    assert week_label(None) is None


def test_week_label_year_at_iso_year_boundary_needs_base44_confirmation():
    # Documents current Python behavior; compare against ecoCalc.js before changing.
    assert week_label(date(2021, 1, 1)) == "21-W53"


def test_current_calculation_rules_for_all_date_based_groups():
    result = compute_eco_fields(
        calculation_row(),
        today=date(2026, 4, 20),
    )

    assert result["gap"] == 17
    assert result["delay_eco_register"] == 2
    assert result["eco_registration_week"] == "26-W14"
    assert result["eco_origem_1"] == 2
    assert result["eco_origem_2"] == 4
    assert result["eco_origem_3"] is None
    assert result["gap_start_az_eco"] == 1
    assert result["contar_eco_emitida_1_dias"] is True
    assert result["gap_agreement"] is None
    assert result["gap_agreement_1"] == 3
    assert result["gap_agreement_2"] == 0
    assert result["gap_agreement_3"] is None
    assert result["gap_total_agreement"] == 3
    assert result["gap_2st_1"] == 10
    assert result["gap_2st_2"] == 4
    assert result["gap_total_2st"] == 14
    assert result["eco_release_week"] == "26-W17"
    assert result["az_gap"] == 18
    assert result["contar_eco_7"] is True
    assert result["contar_eco_10"] is True
    assert result["contar_eco_14"] is True
    assert result["total_gap"] == 21
    assert result["release_month"] == "APR"
    assert result["release_year"] == "26"


@pytest.mark.parametrize(
    ("row_values", "expected"),
    [
        (
            {
                "eco": "E43Q300001",
                "status": "RELEASED",
                "hq_eco_release_date": date(2026, 3, 3),
                "az_eco_register_date": date(2026, 3, 3),
                "az_eco_creation_date": date(2026, 3, 3),
                "agreement_start_1": date(2026, 3, 3),
                "agreement_finish_1": date(2026, 3, 10),
                "second_aprov_rd_start_1": date(2026, 3, 10),
                "second_aprov_rd_finish_1": date(2026, 3, 10),
                "second_aprov_rd_start_2": None,
                "second_aprov_rd_finish_2": None,
            },
            {
                "delay_eco_register": 0,
                "eco_registration_week": "26-W10",
                "gap_start_az_eco": 0,
                "contar_eco_emitida_1_dias": False,
                "gap_agreement": None,
                "gap_agreement_1": 7,
                "gap_total_agreement": 7,
                "gap_2st_1": 0,
                "gap_total_2st": 0,
                "eco_release_week": "26-W11",
                "az_gap": 7,
                "contar_eco_7": False,
                "contar_eco_10": False,
                "total_gap": 7,
                "release_month": "MAR",
                "release_year": "26",
                "gap": "OK",
            },
        ),
        (
            {
                "eco": "ENMP900015",
                "status": "RELEASED",
                "hq_eco_release_date": date(2025, 9, 10),
                "az_eco_register_date": date(2025, 9, 10),
                "az_eco_creation_date": date(2025, 12, 16),
                "agreement_start_1": date(2025, 12, 16),
                "agreement_finish_1": date(2026, 1, 1),
                "second_aprov_rd_start_1": date(2026, 1, 1),
                "second_aprov_rd_finish_1": date(2026, 1, 1),
                "second_aprov_rd_start_2": None,
                "second_aprov_rd_finish_2": None,
            },
            {
                "delay_eco_register": 0,
                "eco_registration_week": "25-W37",
                "gap_start_az_eco": 97,
                "contar_eco_emitida_1_dias": True,
                "gap_agreement": None,
                "gap_agreement_1": 16,
                "gap_total_agreement": 16,
                "gap_2st_1": 0,
                "gap_total_2st": 0,
                "eco_release_week": "26-W01",
                "az_gap": 16,
                "contar_eco_7": True,
                "contar_eco_10": True,
                "total_gap": 113,
                "release_month": "JAN",
                "release_year": "26",
                "gap": "OK",
            },
        ),
        (
            {
                "eco": "DNMP600577",
                "status": "RELEASED",
                "hq_eco_release_date": date(2025, 6, 30),
                "az_eco_register_date": date(2025, 7, 1),
                "az_eco_creation_date": date(2026, 2, 4),
                "agreement_start_1": date(2026, 2, 4),
                "agreement_finish_1": date(2026, 2, 6),
                "second_aprov_rd_start_1": date(2026, 2, 6),
                "second_aprov_rd_finish_1": date(2026, 2, 6),
                "second_aprov_rd_start_2": None,
                "second_aprov_rd_finish_2": None,
            },
            {
                "delay_eco_register": 1,
                "eco_registration_week": "25-W27",
                "gap_start_az_eco": 218,
                "contar_eco_emitida_1_dias": True,
                "gap_agreement": None,
                "gap_agreement_1": 2,
                "gap_total_agreement": 2,
                "gap_2st_1": 0,
                "gap_total_2st": 0,
                "eco_release_week": "26-W06",
                "az_gap": 2,
                "contar_eco_7": False,
                "contar_eco_10": False,
                "total_gap": 221,
                "release_month": "FEB",
                "release_year": "26",
                "gap": "OK",
            },
        ),
        (
            {
                "eco": "ENMPA00276",
                "status": "RELEASED",
                "hq_eco_release_date": date(2025, 11, 5),
                "az_eco_register_date": date(2025, 11, 12),
                "az_eco_creation_date": date(2025, 11, 14),
                "agreement_start_1": date(2025, 11, 14),
                "agreement_finish_1": date(2025, 11, 24),
                "second_aprov_rd_start_1": date(2025, 11, 24),
                "second_aprov_rd_finish_1": date(2025, 11, 25),
                "second_aprov_rd_start_2": None,
                "second_aprov_rd_finish_2": None,
            },
            {
                "delay_eco_register": 7,
                "eco_registration_week": "25-W46",
                "gap_start_az_eco": 2,
                "contar_eco_emitida_1_dias": True,
                "gap_agreement": None,
                "gap_agreement_1": 10,
                "gap_total_agreement": 10,
                "gap_2st_1": 1,
                "gap_total_2st": 1,
                "eco_release_week": "25-W48",
                "az_gap": 11,
                "contar_eco_7": True,
                "contar_eco_10": True,
                "total_gap": 20,
                "release_month": "NOV",
                "release_year": "25",
                "gap": "OK",
            },
        ),
    ],
)
def test_base44_reference_rows_match_current_python_rules(row_values, expected):
    # These values were transcribed from the Base44 table provided for comparison.
    result = compute_eco_fields(
        calculation_row(**row_values),
        today=date(2026, 9, 30),
    )

    for field, expected_value in expected.items():
        assert result[field] == expected_value, field


@pytest.mark.parametrize(
    ("elapsed_days", "count_7", "count_10", "count_14"),
    [
        (7, False, False, False),
        (8, True, False, False),
        (10, True, False, False),
        (11, True, True, False),
        (14, True, True, False),
        (15, True, True, True),
    ],
)
def test_current_release_thresholds(
    elapsed_days,
    count_7,
    count_10,
    count_14,
):
    release_date = date(2026, 4, 4) + timedelta(days=elapsed_days)
    row = calculation_row(
        az_eco_creation_date=date(2026, 4, 4),
        second_aprov_rd_finish_1=release_date,
    )

    result = compute_eco_fields(row, today=date(2026, 4, 30))

    assert result["az_gap"] == elapsed_days
    assert result["contar_eco_7"] is count_7
    assert result["contar_eco_10"] is count_10
    assert result["contar_eco_14"] is count_14


@pytest.mark.parametrize("status", ["RELEASED", "CANCELLED"])
def test_current_gap_returns_ok_for_terminal_status(status):
    result = compute_eco_fields(
        calculation_row(status=status),
        today=date(2026, 4, 20),
    )

    assert result["gap"] == "OK"


def test_current_gap_is_empty_without_eco_or_register_date():
    empty_eco = compute_eco_fields(
        calculation_row(eco=None),
        today=date(2026, 4, 20),
    )
    no_register_date = compute_eco_fields(
        calculation_row(az_eco_register_date=None),
        today=date(2026, 4, 20),
    )

    assert empty_eco["gap"] == ""
    assert no_register_date["gap"] == ""


@pytest.mark.parametrize("status", OPEN_STATUSES)
def test_current_gap_agreement_is_not_calculated_for_open_statuses(status):
    result = compute_eco_fields(
        calculation_row(status=status),
        today=date(2026, 4, 20),
    )

    assert result["gap_agreement"] is None


def test_current_gap_agreement_uses_injected_today_for_non_open_status():
    result = compute_eco_fields(
        calculation_row(status="DONE"),
        today=date(2026, 4, 20),
    )

    assert result["gap_agreement"] == 15


def test_missing_dates_and_empty_aggregates_remain_none():
    result = compute_eco_fields(
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
        today=date(2026, 4, 20),
    )

    assert result["delay_eco_register"] is None
    assert result["eco_origem_1"] is None
    assert result["gap_total_agreement"] is None
    assert result["gap_total_2st"] is None
    assert result["eco_release_week"] == "-"
    assert result["release_month"] == "-"
    assert result["release_year"] == "-"
    assert sum_ignoring_none([None, None]) is None
    assert sum_ignoring_none([None, 0, 3]) == 3