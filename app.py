from datetime import date, time

from db import Storage
from report import ReportBuilder, validate_shift
from export import get_exporter


class PawsApp:
    def __init__(self):
        self.storage = Storage()

    def add_employee(self, full_name: str, position: str = "") -> dict:
        employee_id = self.storage.next_employee_id()
        employee = {"id": employee_id, "full_name": full_name, "position": position}
        self.storage.employees[employee_id] = employee
        return employee

    def list_employees(self) -> list[dict]:
        return list(self.storage.employees.values())

    def add_shift(self, employee_id: int, shift_date: date,
                  start: time, end: time, description: str = "") -> dict:
        shift = {"employee_id": employee_id, "date": shift_date,
                 "start": start, "end": end, "description": description}
        errors = validate_shift(shift, self.storage)
        if errors:
            raise ValueError("; ".join(errors))
        shift_id = self.storage.next_shift_id()
        shift["id"] = shift_id
        self.storage.shifts[shift_id] = shift
        return shift

    def list_shifts(self, employee_id: int | None = None) -> list[dict]:
        shifts = list(self.storage.shifts.values())
        if employee_id is not None:
            shifts = [s for s in shifts if s["employee_id"] == employee_id]
        return sorted(shifts, key=lambda s: (s["date"], s["start"]))

    def generate_report(self, date_from: date, date_to: date,
                         employee_id: int | None = None) -> dict:
        shifts = [
            s for s in self.storage.shifts.values()
            if date_from <= s["date"] <= date_to
            and (employee_id is None or s["employee_id"] == employee_id)
        ]
        shifts.sort(key=lambda s: (s["date"], s["start"]))

        if employee_id is not None:
            employee = self.storage.employees.get(employee_id)
            title = f"Отчёт по сотруднику: {employee['full_name'] if employee else employee_id}"
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