from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config.database import get_db
from app.models.entities import Eco
from app.services.dashboard_service import DashboardService
from app.utils.security import current_user
from main import app


def eco(item, month, year, status, group_name, release_day):
    return Eco(
        item=item,
        month=month,
        status=status,
        group_name=group_name,
        eco=f"ECO-{item}",
        az_eco_register_date=date(year, {
            "JAN": 1,
            "FEB": 2,
            "NOV": 11,
            "DEC": 12,
        }[month], 3),
        second_aprov_rd_finish_1=date(
            year,
            {"JAN": 1, "FEB": 2, "NOV": 11, "DEC": 12}[month],
            release_day,
        ),
    )


@pytest.fixture
def dashboard_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Eco.__table__.create(engine)

    rows = [
        eco(1, "NOV", 2025, "WORKING", "TEAM-A", 10),
        eco(2, "NOV", 2026, "RELEASED", "TEAM-B", 4),
        eco(3, "DEC", 2025, "PROCESSING", "TEAM-A", 18),
        eco(4, "JAN", 2026, "WORKING", "TEAM-B", 8),
        eco(5, "FEB", 2026, "REJECTED", "TEAM-A", 20),
    ]

    with Session(engine) as db:
        db.add_all(rows)
        db.commit()
        yield db

    engine.dispose()


@pytest.fixture
def dashboard_client(dashboard_db):
    overrides_before = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: dashboard_db
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(
        role="admin",
        email="admin@example.com",
    )

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides = overrides_before


def totals_by_name(rows):
    return {row["name"]: row["value"] for row in rows}


def total_delay(rows):
    return sum(row["value"] for row in rows)


def test_stats_are_separated_by_registration_year(dashboard_db):
    service = DashboardService(dashboard_db)

    stats_2025 = service.stats(2025)
    stats_2026 = service.stats(2026)

    assert stats_2025["total"] == 2
    assert stats_2025["working"] == 1
    assert stats_2025["processing"] == 1
    assert stats_2025["released"] == 0

    assert stats_2026["total"] == 3
    assert stats_2026["working"] == 1
    assert stats_2026["released"] == 1
    assert stats_2026["rejected"] == 1


def test_months_only_returns_months_with_ecos_in_selected_year(dashboard_db):
    service = DashboardService(dashboard_db)

    assert service.months(2025) == ["NOV", "DEC"]
    assert service.months(2026) == ["JAN", "FEB", "NOV"]


def test_group_filters_by_year_and_by_year_plus_month(dashboard_db):
    service = DashboardService(dashboard_db)

    assert totals_by_name(service.group("status", year=2026)) == {
        "RELEASED": 1,
        "WORKING": 1,
        "REJECTED": 1,
    }
    assert service.group("status", month="NOV", year=2025) == [
        {"name": "WORKING", "value": 1},
    ]


def test_evolution_only_contains_months_from_selected_year(dashboard_db):
    service = DashboardService(dashboard_db)

    assert totals_by_name(service.evolution(2025)) == {
        "NOV": 1,
        "DEC": 1,
    }
    assert totals_by_name(service.evolution(2026)) == {
        "JAN": 1,
        "FEB": 1,
        "NOV": 1,
    }


def test_delay_filters_by_year_and_by_year_plus_month(dashboard_db):
    service = DashboardService(dashboard_db)

    assert total_delay(service.delay(year=2025)) == 2
    assert total_delay(service.delay(year=2026)) == 3
    assert total_delay(service.delay(month="FEB", year=2026)) == 1


def test_monthly_summary_only_contains_selected_year(dashboard_db):
    service = DashboardService(dashboard_db)

    assert [row["month"] for row in service.monthly_summary(2025)] == [
        "NOV",
        "DEC",
    ]
    assert [row["month"] for row in service.monthly_summary(2026)] == [
        "JAN",
        "FEB",
        "NOV",
    ]


def test_dashboard_year_endpoints_and_year_query_parameters(dashboard_client):
    assert dashboard_client.get("/api/v1/dashboard/years").json() == [
        2026,
        2025,
    ]

    stats = dashboard_client.get(
        "/api/v1/dashboard/stats",
        params={"year": 2026},
    )
    months = dashboard_client.get(
        "/api/v1/dashboard/months",
        params={"year": 2025},
    )
    group = dashboard_client.get(
        "/api/v1/dashboard/group/status",
        params={"year": 2025, "month": "NOV"},
    )
    evolution = dashboard_client.get(
        "/api/v1/dashboard/evolution",
        params={"year": 2026},
    )
    delay = dashboard_client.get(
        "/api/v1/dashboard/delay",
        params={"year": 2026, "month": "FEB"},
    )
    summary = dashboard_client.get(
        "/api/v1/dashboard/monthly-summary",
        params={"year": 2026},
    )

    assert stats.status_code == 200
    assert stats.json()["total"] == 3
    assert months.status_code == 200
    assert months.json() == ["NOV", "DEC"]
    assert group.status_code == 200
    assert group.json() == [{"name": "WORKING", "value": 1}]
    assert evolution.status_code == 200
    assert totals_by_name(evolution.json()) == {
        "JAN": 1,
        "FEB": 1,
        "NOV": 1,
    }
    assert delay.status_code == 200
    assert total_delay(delay.json()) == 1
    assert summary.status_code == 200
    assert [row["month"] for row in summary.json()] == [
        "JAN",
        "FEB",
        "NOV",
    ]
