from datetime import date, datetime, timedelta

from db import Storage

def calculate_duration(shift: dict) -> float:
    start_dt = datetime.combine(shift["date"], shift["start"])
    end_dt = datetime.combine(shift["date"], shift["end"])
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return round((end_dt - start_dt).total_seconds() / 3600, 2)


def validate_shift(shift: dict, storage: Storage) -> list[str]:

    errors = []

    if shift["employee_id"] not in storage.employees:
        errors.append("Сотрудник с таким ID не найден")

    if shift["start"] == shift["end"]:
        errors.append("Время начала и окончания смены совпадает")

    if calculate_duration(shift) > 24:
        errors.append("Смена не может длиться больше 24 часов")

    for other in storage.shifts.values():
        if other["employee_id"] == shift["employee_id"] and other["date"] == shift["date"]:
            errors.append(
                f"У сотрудника уже есть смена {other['date']} "
                f"({other['start']}-{other['end']})"
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

    def add_table(self, shifts: list[dict], employees: dict) -> None:
        self.lines.append(f"{'Сотрудник':22} {'Дата':11} {'Начало':7} {'Конец':7} {'Часы':6}")
        for shift in shifts:
            employee = employees.get(shift["employee_id"])
            name = employee["full_name"] if employee else "?"
            hours = calculate_duration(shift)
            self.rows.append((name, str(shift["date"]), str(shift["start"]),
                               str(shift["end"]), hours, shift["description"]))
            self.lines.append(
                f"{name:22} {str(shift['date']):11} {str(shift['start']):7} "
                f"{str(shift['end']):7} {hours:<6}"
            )

    def add_totals(self, shifts: list[dict]) -> None:
        total_hours = round(sum(calculate_duration(s) for s in shifts), 2)
        self.lines.append("-" * 60)
        self.lines.append(f"Всего смен: {len(shifts)}   Всего часов: {total_hours}")
        self.totals = {"total_shifts": len(shifts), "total_hours": total_hours}

    def build(self) -> dict:
        return {"text": "\n".join(self.lines), "rows": self.rows, "totals": self.totals}