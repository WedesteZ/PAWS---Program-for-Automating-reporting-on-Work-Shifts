"""Тесты API-роутера отчётов (/api/reports)."""

from collections.abc import Callable
from datetime import date
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.models import Report


def test_generate_report_unauthorized(api_client: TestClient) -> None:
    """Проверяет отказ 401 при генерации отчёта без сессии."""
    response = api_client.post(
        "/api/reports/generate",
        json={"date_from": "2026-11-01", "date_to": "2026-11-30"},
    )
    assert response.status_code == 401


def test_generate_report_employee_forced_to_own_id(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    login_as: Callable[..., UUID | str],
    test_report: Report,
) -> None:
    """Проверяет, что employee всегда получает отчёт только по своему ID."""
    mock_core, _ = api_mocks
    mock_core.generate_report.return_value = test_report

    own_id = uuid4()
    other_id = uuid4()
    login_as(role="employee", employee_id=own_id)

    response = api_client.post(
        "/api/reports/generate",
        json={
            "date_from": "2026-11-01",
            "date_to": "2026-11-30",
            "employee_id": str(other_id),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == test_report.title
    assert body["total_shifts"] == 1
    assert body["total_hours"] == 9.0
    mock_core.generate_report.assert_called_once_with(
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 30),
        employee_id=own_id,
    )


def test_generate_report_employee_stale_session_returns_401(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    login_as: Callable[..., UUID | str],
) -> None:
    """Проверяет возврат 401 для employee при отсутствии user_id в сессии."""
    mock_core, _ = api_mocks
    login_as(role="employee", employee_id="")

    response = api_client.post(
        "/api/reports/generate",
        json={"date_from": "2026-11-01", "date_to": "2026-11-30"},
    )

    assert response.status_code == 401
    mock_core.generate_report.assert_not_called()


def test_generate_report_manager_can_query_all_or_specific(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    login_as: Callable[..., UUID | str],
    test_report: Report,
) -> None:
    """Проверяет, что manager может запросить общий отчёт и отчёт по ID."""
    mock_core, _ = api_mocks
    mock_core.generate_report.return_value = test_report
    login_as(role="manager")

    all_resp = api_client.post(
        "/api/reports/generate",
        json={"date_from": "2026-11-01", "date_to": "2026-11-30"},
    )
    assert all_resp.status_code == 200
    mock_core.generate_report.assert_called_with(
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 30),
        employee_id=None,
    )

    target_id = uuid4()
    one_resp = api_client.post(
        "/api/reports/generate",
        json={
            "date_from": "2026-11-01",
            "date_to": "2026-11-30",
            "employee_id": str(target_id),
        },
    )
    assert one_resp.status_code == 200
    mock_core.generate_report.assert_called_with(
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 30),
        employee_id=target_id,
    )


def test_generate_report_business_error_returns_400(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    login_as: Callable[..., UUID | str],
) -> None:
    """Проверяет преобразование ValueError при генерации отчёта в 400."""
    mock_core, _ = api_mocks
    mock_core.generate_report.side_effect = ValueError("Слишком большой период")
    login_as(role="admin")

    response = api_client.post(
        "/api/reports/generate",
        json={"date_from": "2026-11-01", "date_to": "2026-11-30"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Слишком большой период"}


def test_generate_report_inverted_dates_returns_422(
    api_client: TestClient,
    login_as: Callable[..., UUID | str],
) -> None:
    """Проверяет возврат 422 при date_from позже date_to."""
    login_as(role="admin")

    response = api_client.post(
        "/api/reports/generate",
        json={"date_from": "2026-11-30", "date_to": "2026-11-01"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()
