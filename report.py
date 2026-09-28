from datetime import date

from db import Storage
from models import Shift


def calculate_duration(shift: Shift) -> float:
    return shift.calculate_duration


def validate_shift(shift: Shift, storage: Storage) -> list[str]:

    errors = []

    if shift.employee_id not in storage.employees:
        errors.append("Сотрудник с таким ID не найден")

    if shift.time_start == shift.time_end:
        errors.append("Время начала и окончания смены совпадает")

    if shift.calculate_duration > 24:
        errors.append("Смена не может длиться больше 24 часов")

    for other in storage.shifts.values():
        if other.employee_id == shift.employee_id and other.shift_date == shift.shift_date:
            errors.append(
                f"У сотрудника уже есть смена {other.shift_date} "
                f"({other.time_start}-{other.time_end})"
            )

    return errors


class ReportBuilder:
    def __init__(self):
        self.lines: list[str] = []
        self.rows: list[tuple] = []
        self.totals: dict = {}

    def add_header(self, title: str, date_from: date, date_to: date) -> None:
        self.lines.append(title)
        self.lines.append(f"Период: {date_from} - {date_to}")
        self.lines.append("-" * 60)

    def add_table(self, shifts: list[Shift], employees: dict) -> None:
        self.lines.append(f"{'Сотрудник':22} {'Дата':11} {'Начало':7} {'Конец':7} {'Часы':6}")
        for shift in shifts:
            employee = employees.get(shift.employee_id)
            name = employee.full_name if employee else "?"
            hours = shift.calculate_duration
            self.rows.append((name, str(shift.shift_date), str(shift.time_start),
                               str(shift.time_end), hours, shift.description))
            self.lines.append(
                f"{name:22} {str(shift.shift_date):11} {str(shift.time_start):7} "
                f"{str(shift.time_end):7} {hours:<6}"
            )

    def add_totals(self, shifts: list[Shift]) -> None:
        total_hours = round(sum(s.calculate_duration for s in shifts), 2)
        self.lines.append("-" * 60)
        self.lines.append(f"Всего смен: {len(shifts)}   Всего часов: {total_hours}")
        self.totals = {"total_shifts": len(shifts), "total_hours": total_hours}

    def build(self) -> dict:
        return {"text": "\n".join(self.lines), "rows": self.rows, "totals": self.totals}