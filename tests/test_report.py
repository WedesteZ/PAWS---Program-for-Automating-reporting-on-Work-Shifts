import uuid
from datetime import date, time

from src.models import Employee, Shift
from src.report import ReportBuilder


def test_report_builder_empty():
    """Пустой список смен: rows == [], total_shifts == 0, total_hours == 0"""
    builder = ReportBuilder()
    builder.add_table([], {})
    builder.add_totals([])
    report = builder.build()

    assert report.rows == []
    assert report.total_shifts == 0
    assert report.total_hours == 0.0


def test_report_builder_two_shifts():
    """Две смены: сумма часов, количество, порядок строк"""
    emp_id = uuid.uuid4()
    emp = Employee(full_name="Иванов Иван", position="Оператор")
    emp.id = emp_id

    shift1 = Shift.from_times(
        employee_id=emp_id,
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(13, 0),
    )
    shift2 = Shift.from_times(
        employee_id=emp_id,
        shift_date=date(2026, 11, 12),
        start=time(10, 0),
        end=time(18, 0),
    )

    builder = ReportBuilder()
    builder.add_table([shift1, shift2], {emp_id: emp})
    builder.add_totals([shift1, shift2])
    report = builder.build()

    assert report.total_shifts == 2
    assert report.total_hours == 12.0
    assert len(report.rows) == 2
    assert report.rows[0].shift_date == date(2026, 11, 11)
    assert report.rows[1].shift_date == date(2026, 11, 12)


def test_report_builder_unknown_employee():
    """Неизвестный сотрудник даёт имя '?'"""
    shift = Shift.from_times(
        employee_id=uuid.uuid4(),
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
    )

    builder = ReportBuilder()
    builder.add_table([shift], {})
    report = builder.build()

    assert len(report.rows) == 1
    assert report.rows[0].employee == "?"


def test_report_builder_header():
    """period в формате ДД.ММ.ГГГГ - ДД.ММ.ГГГГ, title совпадает с переданным"""
    builder = ReportBuilder()
    builder.add_header(
        title="Ежемесячный отчёт", date_from=date(2026, 1, 5), date_to=date(2026, 1, 15)
    )
    report = builder.build()

    assert report.title == "Ежемесячный отчёт"
    assert report.period == "05.01.2026 - 15.01.2026"
