import uuid
from datetime import date, time
from unittest.mock import MagicMock

import pytest

from src.models import Employee
from src.services.employees import EmployeeService
from src.services.reports import ReportService
from src.services.shifts import ShiftService


@pytest.fixture
def mock_session_factory():
    """Фальшивая фабрика сессий, где .begin() работает как менеджер контекста"""
    factory = MagicMock()
    factory.begin.return_value.__enter__.return_value = MagicMock()
    return factory


def test_employee_service_add_invalid_raises_before_session(mock_session_factory):
    """Пустое ФИО и должность дают ValueError, ошибка бросается до открытия сессии"""
    service = EmployeeService(mock_session_factory)

    with pytest.raises(ValueError):
        service.add(full_name="", position="Оператор")

    with pytest.raises(ValueError):
        service.add(full_name="Иванов Иван", position="")

    mock_session_factory.begin.assert_not_called()


def test_employee_service_add_normalizes_spaces(monkeypatch, mock_session_factory):
    """Пробелы в ФИО нормализуются"""
    mock_repo = MagicMock()
    mock_repo.add.side_effect = lambda employee: employee

    monkeypatch.setattr(
        "src.services.employees.EmployeeRepository", MagicMock(return_value=mock_repo)
    )

    service = EmployeeService(mock_session_factory)
    emp = service.add(full_name="  Иванов    Иван  ", position="  Оператор  ")

    assert emp.full_name == "Иванов Иван"
    assert emp.position == "Оператор"


def test_shift_service_add_employee_not_found(monkeypatch, mock_session_factory):
    """Сотрудник не найден"""
    mock_emp_repo = MagicMock()
    mock_emp_repo.get.return_value = None
    monkeypatch.setattr(
        "src.services.shifts.EmployeeRepository", MagicMock(return_value=mock_emp_repo)
    )

    service = ShiftService(mock_session_factory)

    with pytest.raises(ValueError):
        service.add(
            employee_id=uuid.uuid4(),
            shift_date=date(2026, 11, 11),
            start=time(9, 0),
            end=time(18, 0),
        )


def test_shift_service_add_overlapping(monkeypatch, mock_session_factory, test_shift):
    """Пересечение смен"""
    mock_emp_repo = MagicMock()
    mock_emp_repo.get.return_value = MagicMock()
    monkeypatch.setattr(
        "src.services.shifts.EmployeeRepository", MagicMock(return_value=mock_emp_repo)
    )

    mock_shift_repo = MagicMock()
    mock_shift_repo.find_overlapping.return_value = [test_shift]
    monkeypatch.setattr(
        "src.services.shifts.ShiftRepository", MagicMock(return_value=mock_shift_repo)
    )

    service = ShiftService(mock_session_factory)

    with pytest.raises(ValueError):
        service.add(
            employee_id=uuid.uuid4(),
            shift_date=date(2026, 11, 11),
            start=time(9, 0),
            end=time(18, 0),
        )


def test_shift_service_add_success(monkeypatch, mock_session_factory):
    """Успешное добавление"""
    mock_emp_repo = MagicMock()
    mock_emp_repo.get.return_value = MagicMock()
    monkeypatch.setattr(
        "src.services.shifts.EmployeeRepository", MagicMock(return_value=mock_emp_repo)
    )

    mock_shift_repo = MagicMock()
    mock_shift_repo.find_overlapping.return_value = []
    monkeypatch.setattr(
        "src.services.shifts.ShiftRepository", MagicMock(return_value=mock_shift_repo)
    )

    service = ShiftService(mock_session_factory)

    shift = service.add(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
    )

    assert shift is not None
    mock_shift_repo.add.assert_called_once()


def test_report_service_generate_invalid_dates(mock_session_factory):
    """Дата «с» позже даты «по» бросает ValueError"""
    service = ReportService(mock_session_factory)

    with pytest.raises(ValueError):
        service.generate(date_from=date(2026, 11, 15), date_to=date(2026, 11, 10))


def test_report_service_generate_success(monkeypatch, mock_session_factory):
    """Обычный период формирует отчёт с нужным заголовком (для одного и для всех)"""
    mock_shift_repo = MagicMock()
    mock_shift_repo.get_for_period.return_value = []
    monkeypatch.setattr(
        "src.services.reports.ShiftRepository", MagicMock(return_value=mock_shift_repo)
    )

    mock_emp_repo = MagicMock()
    mock_emp_repo.get_all.return_value = {}
    monkeypatch.setattr(
        "src.services.reports.EmployeeRepository", MagicMock(return_value=mock_emp_repo)
    )

    service = ReportService(mock_session_factory)

    report_all = service.generate(
        date_from=date(2026, 11, 1), date_to=date(2026, 11, 30)
    )
    assert len(report_all.title) > 0

    emp_id = uuid.uuid4()
    mock_emp_repo.get.return_value = Employee(
        full_name="Иванов Иван", position="Оператор"
    )

    report_one = service.generate(
        date_from=date(2026, 11, 1), date_to=date(2026, 11, 30), employee_id=emp_id
    )
    assert len(report_one.title) > 0
