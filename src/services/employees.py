"""Сервис сотрудников."""

from sqlalchemy.orm import Session, sessionmaker

from src.models import Employee
from src.repositories import EmployeeRepository
from src.validation import validate_full_name, validate_position


class EmployeeService:
    """Бизнес-логика работы с сотрудниками."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def add(self, full_name: str, position: str = "") -> Employee:
        """Создаёт сотрудника после проверки ФИО и должности.

        Лишние пробелы в ФИО и должности убираются.

        Raises:
            ValueError: если ФИО или должность не прошли проверку.
        """
        full_name = " ".join(full_name.split())
        position = position.strip()
        errors = validate_full_name(full_name) + validate_position(position)
        if errors:
            raise ValueError("; ".join(errors))
        employee = Employee(full_name=full_name, position=position)
        with self.session_factory.begin() as session:
            return EmployeeRepository(session).add(employee)

    def list_all(self) -> list[Employee]:
        """Возвращает всех сотрудников, отсортированных по ФИО."""
        with self.session_factory() as session:
            return EmployeeRepository(session).list_all()
