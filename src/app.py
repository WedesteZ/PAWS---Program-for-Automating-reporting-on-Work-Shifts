import uuid
from datetime import date, time

from sqlalchemy.orm import Session, sessionmaker

from src.database import SessionLocal
from src.export import get_exporter
from src.models import Employee, Report, Shift
from src.report import ReportBuilder
from src.repositories import EmployeeRepository, ShiftRepository
from src.validation import validate_shift


class PawsApp:
    """Основной класс приложения: сотрудники, смены и отчёты."""

    def __init__(
        self, session_factory: sessionmaker[Session] = SessionLocal
    ) -> None:
        self.session_factory = session_factory

    def add_employee(self, full_name: str, position: str = "") -> Employee:
        """Создаёт нового сотрудника и сохраняет его в базе данных."""
        employee = Employee(full_name=full_name, position=position)
        with self.session_factory.begin() as session:
            return EmployeeRepository(session).add(employee)

    def list_employees(self) -> list[Employee]:
        """Возвращает список всех сотрудников."""
        with self.session_factory() as session:
            return EmployeeRepository(session).list_all()

    def add_shift(
        self,
        employee_id: uuid.UUID,
        shift_date: date,
        start: time,
        end: time,
        description: str = "",
    ) -> Shift:
        """Создаёт новую смену после проверки корректности.

        Raises:
            ValueError: если смена не прошла валидацию.
        """
        shift = Shift.from_times(employee_id, shift_date, start, end, description)
        with self.session_factory.begin() as session:
            employees = EmployeeRepository(session)
            shifts = ShiftRepository(session)
            errors = validate_shift(shift, employees, shifts)
            if errors:
                raise ValueError("; ".join(errors))
            return shifts.add(shift)

    def list_shifts(self, employee_id: uuid.UUID | None = None) -> list[Shift]:
        """Возвращает смены сотрудника (или все смены), отсортированные по началу."""
        with self.session_factory() as session:
            return ShiftRepository(session).list_all(employee_id)

    def generate_report(
        self,
        date_from: date,
        date_to: date,
        employee_id: uuid.UUID | None = None,
    ) -> Report:
        """Формирует отчёт по сменам за период (по одному или всем сотрудникам).

        Возвращает объект отчёта.
        """
        with self.session_factory() as session:
            shifts = ShiftRepository(session).list_between(
                date_from, date_to, employee_id
            )
            employees = {e.id: e for e in EmployeeRepository(session).list_all()}

        if employee_id is not None:
            employee = employees.get(employee_id)
            name = employee.full_name if employee else str(employee_id)
            title = f"Отчёт по сотруднику: {name}"
        else:
            title = "Сводный отчёт по всем сотрудникам"

        builder = ReportBuilder()
        builder.add_header(title, date_from, date_to)
        builder.add_table(shifts, employees)
        builder.add_totals(shifts)
        return builder.build()

    def export_report(self, report: Report, fmt: str, filename: str) -> str:
        """Сохраняет отчёт в файл выбранного формата. Возвращает имя файла."""
        exporter = get_exporter(fmt)
        return exporter.export(report, filename)
