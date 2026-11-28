"""Тесты API-роутера сотрудников (/api/employees)."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from src.models import Employee


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


def test_get_employees_unauthorized(api_client: TestClient) -> None:
    """Проверяет отказ 401 при запросе списка сотрудников без сессии."""
    response = api_client.get("/api/employees")
    assert response.status_code == 401


def test_get_employees_success(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
) -> None:
    """Проверяет получение списка сотрудников авторизованным пользователем."""
    mock_core, mock_auth = api_mocks
    mock_core.list_employees.return_value = [test_employee]
    _login_as(api_client, mock_auth, role="employee")

    response = api_client.get("/api/employees")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(test_employee.id),
            "full_name": test_employee.full_name,
            "position": test_employee.position,
        }
    ]


def test_create_employee_unauthorized(api_client: TestClient) -> None:
    """Проверяет отказ 401 при создании сотрудника без сессии."""
    response = api_client.post(
        "/api/employees",
        json={"full_name": "Петров Пётр", "position": "Инженер"},
    )
    assert response.status_code == 401


def test_create_employee_forbidden_for_employee_role(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет отказ 403 при попытке создать сотрудника под ролью employee."""
    mock_core, mock_auth = api_mocks
    _login_as(api_client, mock_auth, role="employee")

    response = api_client.post(
        "/api/employees",
        json={"full_name": "Петров Пётр", "position": "Инженер"},
    )

    assert response.status_code == 403
    mock_core.add_employee.assert_not_called()


def test_create_employee_success_for_manager(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
) -> None:
    """Проверяет создание сотрудника (201) под ролью manager."""
    mock_core, mock_auth = api_mocks
    mock_core.add_employee.return_value = test_employee
    _login_as(api_client, mock_auth, role="manager")

    response = api_client.post(
        "/api/employees",
        json={"full_name": "  Иванов Иван  ", "position": "  Оператор  "},
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(test_employee.id)
    mock_core.add_employee.assert_called_once_with(
        full_name="Иванов Иван",
        position="Оператор",
    )


def test_create_employee_business_error_returns_400(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет преобразование ValueError сервисного слоя в HTTP 400."""
    mock_core, mock_auth = api_mocks
    mock_core.add_employee.side_effect = ValueError("Некорректное ФИО")
    _login_as(api_client, mock_auth, role="admin")

    response = api_client.post(
        "/api/employees",
        json={"full_name": "Иванов Иван", "position": "Оператор"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Некорректное ФИО"}


def test_create_employee_validation_error_returns_422(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет возврат 422 при невалидных данных сотрудника."""
    _, mock_auth = api_mocks
    _login_as(api_client, mock_auth, role="admin")

    response = api_client.post(
        "/api/employees",
        json={"full_name": "А", "position": ""},
    )

    assert response.status_code == 422
    assert "detail" in response.json()
