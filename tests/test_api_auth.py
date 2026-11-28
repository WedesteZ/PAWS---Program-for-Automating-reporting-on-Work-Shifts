"""Тесты API-роутера аутентификации (/api/auth)."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient


def test_api_login_success(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет успешный вход и создание сессии."""
    _, mock_auth = api_mocks
    mock_auth.login.return_value = SimpleNamespace(
        username="admin",
        role=SimpleNamespace(value="admin"),
        employee_id=uuid4(),
    )

    response = api_client.post(
        "/api/auth/login",
        json={"username": "  admin  ", "password": "secret"},
    )

    assert response.status_code == 200
    assert response.json() == {"username": "admin", "role": "admin"}
    mock_auth.login.assert_called_once_with("admin", "secret")
    assert "session" in api_client.cookies


def test_api_login_invalid_credentials(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет возврат 401 при неверном логине или пароле."""
    _, mock_auth = api_mocks
    mock_auth.login.side_effect = ValueError("Неверный логин или пароль")

    response = api_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Неверный логин или пароль"}


def test_api_login_validation_error(api_client: TestClient) -> None:
    """Проверяет возврат 422 при нарушении ограничений DTO."""
    response = api_client.post(
        "/api/auth/login",
        json={"username": "ab", "password": "12"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()
