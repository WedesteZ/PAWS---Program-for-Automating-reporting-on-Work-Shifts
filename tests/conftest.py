import os
from datetime import date, time

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")

from unittest.mock import MagicMock

import pytest

from src.models import Employee, Report, ReportRow, Shift


@pytest.fixture
def test_employee() -> Employee:
    return Employee(full_name="Иванов Иван", position="Оператор")


@pytest.fixture
def test_shift(test_employee: Employee) -> Shift:
    return Shift.from_times(
        employee_id=test_employee.id,
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
        description="Тестовая работа"
    )


@pytest.fixture
def test_report(test_employee: Employee) -> Report:
    row = ReportRow(
        employee=test_employee.full_name,
        shift_date=date(2026, 11, 11),
        time_start=time(9, 0),
        time_end=time(18, 0),
        hours=9.0,
        description="Тестовая работа"
    )
    return Report(
        text="Тестовый отчёт",
        rows=[row],
        total_shifts=1,
        total_hours=9.0
    )


@pytest.fixture
def mock_session_factory() -> MagicMock:
    """Фальшивая фабрика сессий для подмены БД."""
    factory = MagicMock()
    session_mock = MagicMock()
    factory.begin.return_value.__enter__.return_value = session_mock
    return factory