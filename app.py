from datetime import date, time

from db import Storage
from models import Employee, Shift
from report import ReportBuilder
from export import get_exporter
from validation import validate_shift


class PawsApp:
    """Основной класс приложения: сотрудники, смены и отчёты."""

    def __init__(self) -> None:
        self.storage = Storage()

    def add_employee(self, full_name: str, position: str = "") -> Employee:
        """Создаёт нового сотрудника и сохраняет его в хранилище."""
        employee = Employee(full_name=full_name, position=position)
        return self.storage.add_employee(employee)

    def list_employees(self) -> list[Employee]:
        """Возвращает список всех сотрудников."""
        return list(self.storage.employees.values())

    def add_shift(self, employee_id: str, shift_date: date,
                  start: time, end: time, description: str = "") -> Shift:
        """Создаёт новую смену после проверки корректности.

        Raises:
            ValueError: если смена не прошла валидацию.
        """
        shift = Shift(employee_id=employee_id, shift_date=shift_date,
                      time_start=start, time_end=end, description=description)
        errors = validate_shift(shift, self.storage)
        if errors:
            raise ValueError("; ".join(errors))
        return self.storage.add_shift(shift)

    def list_shifts(self, employee_id: str | None = None) -> list[Shift]:
        """Возвращает смены сотрудника (или все смены), отсортированные по дате."""
        shifts = list(self.storage.shifts.values())
        if employee_id is not None:
            shifts = [s for s in shifts if s.employee_id == employee_id]
        return sorted(shifts, key=lambda s: (s.shift_date, s.time_start))

    def generate_report(self, date_from: date, date_to: date,
                         employee_id: str | None = None) -> dict:
        """Формирует отчёт по сменам за период (по одному или всем сотрудникам).

        Возвращает словарь с ключами 'text', 'rows' и 'totals'.
        """
        shifts = [
            s for s in self.storage.shifts.values()
            if date_from <= s.shift_date <= date_to
            and (employee_id is None or s.employee_id == employee_id)
        ]
        shifts.sort(key=lambda s: (s.shift_date, s.time_start))

        if employee_id is not None:
            employee = self.storage.employees.get(employee_id)
            title = f"Отчёт по сотруднику: {employee.full_name if employee else employee_id}"
        else:
            title = "Сводный отчёт по всем сотрудникам"

        builder = ReportBuilder()
        builder.add_header(title, date_from, date_to)
        builder.add_table(shifts, self.storage.employees)
        builder.add_totals(shifts)
        return builder.build()

    def export_report(self, report: dict, fmt: str, filename: str) -> str:
        """Сохраняет отчёт в файл выбранного формата. Возвращает имя файла."""
        exporter = get_exporter(fmt)
        return exporter.export(report, filename)