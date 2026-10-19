from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config.database import get_db
from app.models.entities import Eco
from app.services.dashboard_service import DashboardService
from app.utils.security import current_user
from main import app


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeDashboardDatabase:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self, statement):
        params = statement.compile().params.values()
        months = [
            value.upper()
            for value in params
            if isinstance(value, str)
            and value.upper() in DashboardService.MONTH_ORDER
        ]
        date_bounds = sorted(
            value
            for value in params
            if isinstance(value, date)
        )

        if not months:
            return FakeScalars(
                [row.az_eco_register_date for row in self.rows]
            )

        month = months[0]
        rows = [
            row
            for row in self.rows
            if row.month and row.month.strip().upper() == month
        ]

        if len(date_bounds) == 2:
            start, end = date_bounds
            rows = [
                row
                for row in rows
                if row.az_eco_register_date is not None
                and start <= row.az_eco_register_date < end
            ]

        return FakeScalars(rows)


@pytest.fixture
def eco_rows():
    return [
        Eco(
            month="NOV",
            status="WORKING",
            az_eco_register_date=date(2025, 11, 10),
        ),
        Eco(
            month="NOV",
            status="RELEASED",
            az_eco_register_date=date(2026, 11, 12),
        ),
        Eco(
            month="DEC",
            status="PROCESSING",
            az_eco_register_date=date(2025, 12, 4),
        ),
        Eco(
            month="JAN",
            status="REJECTED",
            az_eco_register_date=date(2026, 1, 8),
        ),
        Eco(
            month="JAN",
            status="WORKING",
            az_eco_register_date=None,
        ),
    ]


def expected_month(month, status):
    return {
        "month": month,
        "total": 1,
        "working": int(status == "WORKING"),
        "processing": int(status == "PROCESSING"),
        "cancelled": 0,
        "released": int(status == "RELEASED"),
        "rejected": int(status == "REJECTED"),
    }


def test_monthly_summary_filters_registration_date_by_year(eco_rows):
    service = DashboardService(FakeDashboardDatabase(eco_rows))

    summary_2025 = service.monthly_summary(2025)
    summary_2026 = service.monthly_summary(2026)

    assert summary_2025 == [
        expected_month("NOV", "WORKING"),
        expected_month("DEC", "PROCESSING"),
    ]
    assert summary_2026 == [
        expected_month("JAN", "REJECTED"),
        expected_month("NOV", "RELEASED"),
    ]


def test_years_returns_distinct_registration_years_in_descending_order(
    eco_rows,
):
    service = DashboardService(FakeDashboardDatabase(eco_rows))

    assert service.years() == [2026, 2025]


@pytest.fixture
def dashboard_client(eco_rows):
    overrides_before = app.dependency_overrides.copy()
    database = FakeDashboardDatabase(eco_rows)
    app.dependency_overrides[get_db] = lambda: database
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(
        role="admin",
        email="admin@example.com",
    )

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides = overrides_before


def test_dashboard_years_endpoint_returns_available_years(dashboard_client):
    response = dashboard_client.get("/api/v1/dashboard/years")

    assert response.status_code == 200
    assert response.json() == [2026, 2025]


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        (
            2025,
            [
                expected_month("NOV", "WORKING"),
                expected_month("DEC", "PROCESSING"),
            ],
        ),
        (
            2026,
            [
                expected_month("JAN", "REJECTED"),
                expected_month("NOV", "RELEASED"),
            ],
        ),
    ],
)
def test_monthly_summary_endpoint_accepts_year(dashboard_client, year, expected):
    response = dashboard_client.get(
        "/api/v1/dashboard/monthly-summary",
        params={"year": year},
    )

    assert response.status_code == 200
    assert response.json() == expected
