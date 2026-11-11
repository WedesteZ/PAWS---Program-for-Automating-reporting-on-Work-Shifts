import uuid
from datetime import date

from src import Employee, Report, ReportRow, Shift


class ReportBuilder:
    """Построитель отчёта по сменам: заголовок, строки таблицы и итоги."""

    def __init__(self) -> None:
        self.rows: list[ReportRow] = []
        self.title = ""
        self.period = ""
        self.total_shifts = 0
        self.total_hours = 0.0

    def add_header(self, title: str, date_from: date, date_to: date) -> None:
        """Задаёт заголовок отчёта и период."""
        self.title = title
        self.period = f"{date_from:%d.%m.%Y} - {date_to:%d.%m.%Y}"

    def add_table(
        self, shifts: list[Shift], employees: dict[uuid.UUID, Employee]
    ) -> None:
        """Заполняет строки отчёта по сменам."""
        for shift in shifts:
            employee = employees.get(shift.employee_id)
            self.rows.append(
                ReportRow(
                    employee=employee.full_name if employee else "?",
                    shift_date=shift.shift_date,
                    time_start=shift.time_start,
                    time_end=shift.time_end,
                    hours=shift.duration_hours,
                    description=shift.description,
                )
            )

    def add_totals(self, shifts: list[Shift]) -> None:
        """Считает количество смен и сумму часов."""
        self.total_shifts = len(shifts)
        self.total_hours = round(sum(s.duration_hours for s in shifts), 2)

    def build(self) -> Report:
        """Собирает готовый отчёт из накопленных частей."""
        return Report(
            title=self.title,
            period=self.period,
            rows=self.rows,
            total_shifts=self.total_shifts,
            total_hours=self.total_hours,
        )
