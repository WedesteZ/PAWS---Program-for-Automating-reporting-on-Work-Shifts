import uuid
from datetime import date

from src.models import Employee, Report, ReportRow, Shift

NAME_WIDTH = 28


def _short(text: str, width: int) -> str:
    """Обрезает строку до width символов, добавляя многоточие."""
    return text if len(text) <= width else text[: width - 1] + "…"


class ReportBuilder:
    """Построитель отчёта по сменам: текст, строки для экспорта и итоги."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.rows: list[ReportRow] = []
        self.title = ""
        self.period = ""
        self.total_shifts = 0
        self.total_hours = 0.0

    def add_header(self, title: str, date_from: date, date_to: date) -> None:
        """Добавляет заголовок отчёта с периодом."""
        self.title = title
        self.period = f"{date_from:%d.%m.%Y} - {date_to:%d.%m.%Y}"
        self.lines.append(title)
        self.lines.append(f"Период: {self.period}")
        self.lines.append("-" * 70)

    def add_table(
        self, shifts: list[Shift], employees: dict[uuid.UUID, Employee]
    ) -> None:
        """Добавляет таблицу смен и заполняет строки для экспорта."""
        header = f"{'Сотрудник':{NAME_WIDTH}} {'Дата':10} {'Начало':6} {'Конец':6}"
        self.lines.append(f"{header} {'Часы':>6}")
        if not shifts:
            self.lines.append("За выбранный период смен нет.")
        for shift in shifts:
            employee = employees.get(shift.employee_id)
            name = employee.full_name if employee else "?"
            hours = shift.duration_hours
            self.rows.append(
                ReportRow(
                    employee=name,
                    shift_date=shift.shift_date,
                    time_start=shift.time_start,
                    time_end=shift.time_end,
                    hours=hours,
                    description=shift.description,
                )
            )
            self.lines.append(
                f"{_short(name, NAME_WIDTH):{NAME_WIDTH}} "
                f"{shift.shift_date:%d.%m.%Y} "
                f"{shift.time_start:%H:%M}  {shift.time_end:%H:%M}  {hours:>6.2f}"
            )

    def add_totals(self, shifts: list[Shift]) -> None:
        """Добавляет итоговую строку с количеством смен и суммой часов."""
        total_hours = round(sum(s.duration_hours for s in shifts), 2)
        self.lines.append("-" * 70)
        self.lines.append(f"Всего смен: {len(shifts)}   Всего часов: {total_hours}")
        self.total_shifts = len(shifts)
        self.total_hours = total_hours

    def build(self) -> Report:
        """Собирает готовый отчёт из накопленных частей."""
        return Report(
            text="\n".join(self.lines),
            rows=self.rows,
            total_shifts=self.total_shifts,
            total_hours=self.total_hours,
            title=self.title,
            period=self.period,
        )
