"""Юнит-тесты валидаторов и сериализации DTO."""

from datetime import date, time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.dtos.requests import (
    EmployeeCreateRequest,
    LoginRequest,
    ReportRequest,
    ShiftCreateRequest,
)
from src.dtos.responses import (
    EmployeeResponse,
    ReportResponse,
    ShiftResponse,
    UserResponse,
)
from src.models import Employee, Report, Shift


def test_login_request_strips_username() -> None:
    """Проверяет очистку логина от пробелов по краям."""
    dto = LoginRequest(username="  admin  ", password="secret")
    assert dto.username == "admin"
    assert dto.password == "secret"


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("ab", "secret"),
        ("a" * 31, "secret"),
        ("admin", "123"),
        ("admin", "p" * 65),
    ],
)
def test_login_request_invalid_lengths(username: str, password: str) -> None:
    """Проверяет ограничения длины логина и пароля."""
    with pytest.raises(ValidationError):
        LoginRequest(username=username, password=password)


def test_employee_create_request_strips_fields() -> None:
    """Проверяет очистку ФИО и должности от крайних пробелов."""
    dto = EmployeeCreateRequest(
        full_name="  Иванов Иван  ",
        position="  Оператор  ",
    )
    assert dto.full_name == "Иванов Иван"
    assert dto.position == "Оператор"


def test_employee_create_request_invalid_lengths() -> None:
    """Проверяет отклонение слишком короткого ФИО и пустой должности."""
    with pytest.raises(ValidationError):
        EmployeeCreateRequest(full_name="А", position="Оператор")

    with pytest.raises(ValidationError):
        EmployeeCreateRequest(full_name="Иванов Иван", position="")


def test_shift_create_request_valid_and_overnight() -> None:
    """Проверяет допустимость обычной и ночной смены."""
    emp_id = uuid4()
    day_shift = ShiftCreateRequest(
        employee_id=emp_id,
        shift_date=date(2026, 11, 12),
        time_start=time(9, 0),
        time_end=time(17, 0),
        description="Дневная смена",
    )
    night_shift = ShiftCreateRequest(
        employee_id=emp_id,
        shift_date=date(2026, 11, 12),
        time_start=time(22, 0),
        time_end=time(6, 0),
    )
    assert day_shift.description == "Дневная смена"
    assert night_shift.description is None


def test_shift_create_request_equal_times_rejected() -> None:
    """Проверяет запрет совпадающего времени начала и окончания смены."""
    with pytest.raises(ValidationError, match="не может совпадать"):
        ShiftCreateRequest(
            employee_id=uuid4(),
            shift_date=date(2026, 11, 12),
            time_start=time(9, 0),
            time_end=time(9, 0),
        )


def test_shift_create_request_description_max_length() -> None:
    """Проверяет ограничение длины описания смены (255 символов)."""
    with pytest.raises(ValidationError):
        ShiftCreateRequest(
            employee_id=uuid4(),
            shift_date=date(2026, 11, 12),
            time_start=time(9, 0),
            time_end=time(18, 0),
            description="x" * 256,
        )


def test_report_request_valid_and_single_day() -> None:
    """Проверяет корректный период отчёта и отчёт за один день."""
    dto = ReportRequest(date_from=date(2026, 11, 1), date_to=date(2026, 11, 1))
    assert dto.date_from == dto.date_to
    assert dto.employee_id is None


def test_report_request_inverted_dates_rejected() -> None:
    """Проверяет запрет даты начала позже даты окончания."""
    with pytest.raises(ValidationError, match="не может быть позже"):
        ReportRequest(date_from=date(2026, 11, 30), date_to=date(2026, 11, 1))


def test_response_dtos_from_attributes(
    test_employee: Employee,
    test_shift: Shift,
    test_report: Report,
) -> None:
    """Проверяет сборку выходных DTO из доменных объектов."""
    user_dto = UserResponse.model_validate(
        SimpleNamespace(username="admin", role="admin")
    )
    emp_dto = EmployeeResponse.model_validate(test_employee)
    shift_dto = ShiftResponse.model_validate(test_shift)
    report_dto = ReportResponse.model_validate(test_report)

    assert user_dto.username == "admin"
    assert emp_dto.id == test_employee.id
    assert shift_dto.employee_id == test_employee.id
    assert report_dto.total_shifts == 1
    assert len(report_dto.rows) == 1
    assert report_dto.rows[0].employee == test_employee.full_name
