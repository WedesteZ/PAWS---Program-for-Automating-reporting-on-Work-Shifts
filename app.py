from datetime import date, time

from db import Storage
from models import Employee, Role, Shift, User
from report import ReportBuilder, validate_shift
from export import get_exporter


class PawsApp:
    def __init__(self):
        self.storage = Storage()

    def add_employee(self, full_name: str, position: str = "") -> Employee:
        employee = Employee(full_name=full_name, position=position)
        return self.storage.add_employee(employee)

    def list_employees(self) -> list[Employee]:
        return list(self.storage.employees.values())

    def add_user(self, username: str, password: str,
                 employee_id: str, role: Role) -> User:
        if employee_id not in self.storage.employees:
            raise ValueError("Сотрудник с таким ID не найден")
        if username in self.storage.users:
            raise ValueError("Пользователь с таким именем уже существует")
        user = User(username=username, password=password,
                    employee_id=employee_id, role=role)
        return self.storage.add_user(user)

    def add_shift(self, employee_id: str, shift_date: date,
                  start: time, end: time, description: str = "") -> Shift:
        shift = Shift(employee_id=employee_id, shift_date=shift_date,
                      time_start=start, time_end=end, description=description)
        errors = validate_shift(shift, self.storage)
        if errors:
            raise ValueError("; ".join(errors))
        return self.storage.add_shift(shift)

    def list_shifts(self, employee_id: str | None = None) -> list[Shift]:
        shifts = list(self.storage.shifts.values())
        if employee_id is not None:
            shifts = [s for s in shifts if s.employee_id == employee_id]
        return sorted(shifts, key=lambda s: (s.shift_date, s.time_start))

    def generate_report(self, date_from: date, date_to: date,
                         employee_id: str | None = None) -> dict:
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
        exporter = get_exporter(fmt)
        return exporter.export(report, filename)