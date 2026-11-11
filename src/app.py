import uuid
from datetime import date, time

from sqlalchemy.orm import Session, sessionmaker

from src.database import SessionLocal
from src.models import Employee, Report, Shift
from src.services.employees import EmployeeService
from src.services.reports import ReportService
from src.services.shifts import ShiftService


class PawsApp:
    """Фасад над сервисами: сотрудники, смены и отчёты."""

    def __init__(self, session_factory: sessionmaker[Session] = SessionLocal) -> None:
        self.session_factory = session_factory
        self.employees = EmployeeService(session_factory)
        self.shifts = ShiftService(session_factory)
        self.reports = ReportService(session_factory)

    def add_employee(self, full_name: str, position: str = "") -> Employee:
        """Создаёт нового сотрудника и сохраняет его в базе данных."""
        return self.employees.add(full_name, position)

    def list_employees(self) -> list[Employee]:
        """Возвращает список всех сотрудников."""
        return self.employees.list_all()

    def add_shift(
        self,
        employee_id: uuid.UUID,
        shift_date: date,
        start: time,
        end: time,
        description: str = "",
    ) -> Shift:
        """Создаёт новую смену после проверки корректности."""
        return self.shifts.add(employee_id, shift_date, start, end, description)

    def list_shifts(self, employee_id: uuid.UUID | None = None) -> list[Shift]:
        """Возвращает смены сотрудника (или все смены), отсортированные по началу."""
        return self.shifts.list_all(employee_id)

    def generate_report(
        self,
        date_from: date,
        date_to: date,
        employee_id: uuid.UUID | None = None,
    ) -> Report:
        """Формирует отчёт по сменам за период."""
        return self.reports.generate(date_from, date_to, employee_id)

    def export_report(self, report: Report, fmt: str, filename: str) -> str:
        """Сохраняет отчёт в файл выбранного формата. Возвращает имя файла."""
        return self.reports.export(report, fmt, filename)
