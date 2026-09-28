from datetime import date

from models import Employee, Shift


def calculate_duration(shift: Shift) -> float:
    """Возвращает длительность смены в часах (делегирует модели Shift)."""
    return shift.calculate_duration


class ReportBuilder:
    """Построитель отчёта по сменам: текст, строки для CSV и итоги."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.rows: list[tuple] = []
        self.totals: dict = {}

    def add_header(self, title: str, date_from: date, date_to: date) -> None:
        """Добавляет заголовок отчёта с периодом."""
        self.lines.append(title)
        self.lines.append(f"Период: {date_from} - {date_to}")
        self.lines.append("-" * 60)

    def add_table(self, shifts: list[Shift],
                  employees: dict[str, Employee]) -> None:
        """Добавляет таблицу смен и заполняет строки для экспорта в CSV."""
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
        """Добавляет итоговую строку с количеством смен и суммой часов."""
        total_hours = round(sum(s.calculate_duration for s in shifts), 2)
        self.lines.append("-" * 60)
        self.lines.append(f"Всего смен: {len(shifts)}   Всего часов: {total_hours}")
        self.totals = {"total_shifts": len(shifts), "total_hours": total_hours}

    def build(self) -> dict:
        """Собирает отчёт в словарь с ключами 'text', 'rows' и 'totals'."""
        return {"text": "\n".join(self.lines), "rows": self.rows, "totals": self.totals}