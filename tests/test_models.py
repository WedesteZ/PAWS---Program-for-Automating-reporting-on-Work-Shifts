import uuid
from datetime import date, datetime, time

from src.models import Shift


def test_shift_from_times_normal():
    """Проверка обычной дневной смены"""
    shift = Shift.from_times(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
    )
    assert shift.start_at == datetime(2026, 11, 11, 9, 0)
    assert shift.end_at == datetime(2026, 11, 11, 18, 0)
    assert shift.duration_hours == 9.0


def test_shift_from_times_night():
    """Проверка ночной смены с переходом на следующие сутки"""
    shift = Shift.from_times(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(22, 0),
        end=time(6, 0),
    )
    assert shift.start_at == datetime(2026, 11, 11, 22, 0)
    assert shift.end_at == datetime(2026, 11, 12, 6, 0)
    assert shift.duration_hours == 8.0


def test_shift_from_times_equal_start_end():
    """Проверка смены, где начало равно окончанию (считается как 0 часов)"""
    shift = Shift.from_times(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(9, 0),
    )
    assert shift.duration_hours == 0.0


def test_shift_duration_hours_rounding():
    """Проверка округления дробного значения продолжительности смены"""
    shift = Shift.from_times(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(17, 30),
    )
    assert shift.duration_hours == 8.5


def test_shift_description():
    """Проверка поля примечания: по умолчанию и с заданным текстом"""
    shift_empty = Shift.from_times(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
    )
    assert shift_empty.description == ""

    shift_with_text = Shift.from_times(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
        description="Тестовое примечание",
    )
    assert shift_with_text.description == "Тестовое примечание"


def test_shift_properties(test_shift):
    """Проверка свойств, возвращающих дату и время из меток (использует фикстуру)"""
    assert test_shift.shift_date == date(2026, 11, 11)
    assert test_shift.time_start == time(9, 0)
    assert test_shift.time_end == time(18, 0)
