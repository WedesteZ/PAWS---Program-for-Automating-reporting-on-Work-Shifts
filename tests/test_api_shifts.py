"""Тесты API-роутера смен (/api/shifts)."""

from datetime import date, time
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from src.models import Employee, Shift


def _login_as(
    api_client: TestClient,
    mock_auth: MagicMock,
    role: str,
) -> None:
    """Авторизует тестовый клиент с указанной ролью."""
    mock_auth.login.return_value = SimpleNamespace(
        username=f"user_{role}",
        role=SimpleNamespace(value=role),
        employee_id=uuid4(),
    )
    response = api_client.post(
        "/api/auth/login",
        json={"username": f"user_{role}", "password": "secret"},
    )
    assert response.status_code == 200


def test_get_shifts_unauthorized(api_client: TestClient) -> None:
    """Проверяет отказ 401 при запросе смен без сессии."""
    response = api_client.get("/api/shifts")
    assert response.status_code == 401


def test_get_shifts_all_and_filtered(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
    test_shift: Shift,
) -> None:
    """Проверяет получение всех смен и фильтрацию по employee_id."""
    mock_core, mock_auth = api_mocks
    mock_core.list_shifts.return_value = [test_shift]
    _login_as(api_client, mock_auth, role="employee")

    all_response = api_client.get("/api/shifts")
    assert all_response.status_code == 200
    assert all_response.json() == [
        {
            "id": str(test_shift.id),
            "employee_id": str(test_employee.id),
            "shift_date": "2026-11-11",
            "time_start": "09:00:00",
            "time_end": "18:00:00",
            "description": "Тестовая работа",
        }
    ]
    mock_core.list_shifts.assert_called_with(employee_id=None)

    filtered_response = api_client.get(
        "/api/shifts",
        params={"employee_id": str(test_employee.id)},
    )
    assert filtered_response.status_code == 200
    mock_core.list_shifts.assert_called_with(employee_id=test_employee.id)


def test_create_shift_unauthorized(
    api_client: TestClient,
    test_employee: Employee,
) -> None:
    """Проверяет отказ 401 при создании смены без сессии."""
    response = api_client.post(
        "/api/shifts",
        json={
            "employee_id": str(test_employee.id),
            "shift_date": "2026-11-11",
            "time_start": "09:00:00",
            "time_end": "18:00:00",
        },
    )
    assert response.status_code == 401


def test_create_shift_forbidden_for_employee(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
) -> None:
    """Проверяет отказ 403 при попытке создать смену под ролью employee."""
    mock_core, mock_auth = api_mocks
    _login_as(api_client, mock_auth, role="employee")

    response = api_client.post(
        "/api/shifts",
        json={
            "employee_id": str(test_employee.id),
            "shift_date": "2026-11-11",
            "time_start": "09:00:00",
            "time_end": "18:00:00",
        },
    )

    assert response.status_code == 403
    mock_core.add_shift.assert_not_called()


def test_create_shift_success_for_manager(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
    test_shift: Shift,
) -> None:
    """Проверяет создание смены (201) под ролью manager."""
    mock_core, mock_auth = api_mocks
    mock_core.add_shift.return_value = test_shift
    _login_as(api_client, mock_auth, role="manager")

    response = api_client.post(
        "/api/shifts",
        json={
            "employee_id": str(test_employee.id),
            "shift_date": "2026-11-11",
            "time_start": "09:00:00",
            "time_end": "18:00:00",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(test_shift.id)
    mock_core.add_shift.assert_called_once_with(
        employee_id=test_employee.id,
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
        description="",
    )


def test_create_shift_not_found_returns_404(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет возврат 404, если сотрудник не найден."""
    mock_core, mock_auth = api_mocks
    mock_core.add_shift.side_effect = ValueError("Сотрудник не найден")
    _login_as(api_client, mock_auth, role="admin")

    response = api_client.post(
        "/api/shifts",
        json={
            "employee_id": str(uuid4()),
            "shift_date": "2026-11-11",
            "time_start": "09:00:00",
            "time_end": "18:00:00",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Сотрудник не найден"}


def test_create_shift_overlap_returns_409(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет возврат 409 при пересечении смен."""
    mock_core, mock_auth = api_mocks
    mock_core.add_shift.side_effect = ValueError("Смена пересекается с существующей")
    _login_as(api_client, mock_auth, role="admin")

    response = api_client.post(
        "/api/shifts",
        json={
            "employee_id": str(uuid4()),
            "shift_date": "2026-11-11",
            "time_start": "09:00:00",
            "time_end": "18:00:00",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Смена пересекается с существующей"}


def test_create_shift_equal_times_returns_422(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет возврат 422 при совпадающем времени начала и окончания."""
    _, mock_auth = api_mocks
    _login_as(api_client, mock_auth, role="admin")

    response = api_client.post(
        "/api/shifts",
        json={
            "employee_id": str(uuid4()),
            "shift_date": "2026-11-11",
            "time_start": "09:00:00",
            "time_end": "09:00:00",
        },
    )

    assert response.status_code == 422
    assert "detail" in response.json()
