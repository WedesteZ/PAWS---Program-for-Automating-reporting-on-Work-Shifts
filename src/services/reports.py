"""Сервис отчётов."""

import uuid
from datetime import date

from sqlalchemy.orm import Session, sessionmaker

from src.export import get_exporter
from src.models import Employee, Report
from src.report import ReportBuilder
from src.repositories import EmployeeRepository, ShiftRepository


class ReportService:
    """Формирование и экспорт отчётов по сменам."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def generate(
        self,
        date_from: date,
        date_to: date,
        employee_id: uuid.UUID | None = None,
    ) -> Report:
        """Формирует отчёт по сменам за период (по одному или всем сотрудникам).

        Raises:
            ValueError: если дата начала позже даты окончания.
        """
        if date_from > date_to:
            raise ValueError("Дата начала периода позже даты окончания")
        with self.session_factory() as session:
            shifts = ShiftRepository(session).list_between(
                date_from, date_to, employee_id
            )
            employees = {e.id: e for e in EmployeeRepository(session).list_all()}

        builder = ReportBuilder()
        builder.add_header(self._title(employee_id, employees), date_from, date_to)
        builder.add_table(shifts, employees)
        builder.add_totals(shifts)
        return builder.build()

    def export(self, report: Report, fmt: str, filename: str) -> str:
        """Сохраняет отчёт в файл выбранного формата. Возвращает имя файла.

        Raises:
            ValueError: если формат не поддерживается.
        """
        return get_exporter(fmt).export(report, filename)

    @staticmethod
    def _title(
        employee_id: uuid.UUID | None, employees: dict[uuid.UUID, Employee]
    ) -> str:
        """Возвращает заголовок отчёта: по сотруднику или сводный."""
        if employee_id is None:
            return "Сводный отчёт по всем сотрудникам"
        employee = employees.get(employee_id)
        name = employee.full_name if employee else str(employee_id)
        return f"Отчёт по сотруднику: {name}"
