import os
from collections.abc import Callable, Iterator
from datetime import date, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test"
)
os.environ.setdefault("SESSION_SECRET", "test-session-secret-key")

import pytest
from fastapi.testclient import TestClient

from src.models import Employee, Report, ReportRow, Shift


@pytest.fixture
def test_employee() -> Employee:
    """Возвращает тестового сотрудника."""
    return Employee(full_name="Иванов Иван", position="Оператор")


@pytest.fixture
def test_shift(test_employee: Employee) -> Shift:
    """Возвращает тестовую смену."""
    return Shift.from_times(
        employee_id=test_employee.id,
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
        description="Тестовая работа",
    )


@pytest.fixture
def test_report(test_employee: Employee) -> Report:
    """Возвращает тестовый отчёт."""
    row = ReportRow(
        employee=test_employee.full_name,
        shift_date=date(2026, 11, 11),
        time_start=time(9, 0),
        time_end=time(18, 0),
        hours=9.0,
        description="Тестовая работа",
    )
    return Report(
        title="Тестовый отчёт",
        period="11.11.2026 - 11.11.2026",
        rows=[row],
        total_shifts=1,
        total_hours=9.0,
    )


@pytest.fixture
def mock_session_factory() -> MagicMock:
    """Фальшивая фабрика сессий для подмены БД."""
    factory = MagicMock()
    session_mock = MagicMock()
    factory.begin.return_value.enter.return_value = session_mock
    return factory


@pytest.fixture
def api_mocks(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Подменяет paws_core и auth_manager моками во всех веб- и API-модулях."""
    with patch("src.demo.seed_demo_data"):
        import src.api.auth as api_auth
        import src.api.employees as api_employees
        import src.api.reports as api_reports
        import src.api.shifts as api_shifts
        import src.container as container
        import src.main as main_module

    mock_core = MagicMock()
    mock_auth = MagicMock()

    monkeypatch.setattr(container, "paws_core", mock_core)
    monkeypatch.setattr(container, "auth_manager", mock_auth)
    monkeypatch.setattr(main_module, "paws_core", mock_core)
    monkeypatch.setattr(main_module, "auth_manager", mock_auth)
    monkeypatch.setattr(api_auth, "auth_manager", mock_auth)
    monkeypatch.setattr(api_employees, "paws_core", mock_core)
    monkeypatch.setattr(api_shifts, "paws_core", mock_core)
    monkeypatch.setattr(api_reports, "paws_core", mock_core)

    return mock_core, mock_auth


@pytest.fixture
def api_client(api_mocks: tuple[MagicMock, MagicMock]) -> Iterator[TestClient]:
    """Возвращает изолированный TestClient FastAPI без реальной БД."""
    from src.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def login_as(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> Callable[..., UUID | str]:
    """Возвращает хелпер для авторизации TestClient под нужной ролью."""
    _, mock_auth = api_mocks

    def _login(
        role: str = "admin",
        employee_id: UUID | str | None = None,
    ) -> UUID | str:
        emp_id: UUID | str = uuid4() if employee_id is None else employee_id
        mock_auth.login.return_value = SimpleNamespace(
            username=f"user_{role}",
            role=SimpleNamespace(value=role),
            employee_id=emp_id,
        )
        response = api_client.post(
            "/api/auth/login",
            json={"username": f"user_{role}", "password": "secret"},
        )
        assert response.status_code == 200
        return emp_id

    return _login
