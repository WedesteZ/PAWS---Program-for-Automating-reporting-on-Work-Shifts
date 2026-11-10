"""Сервис рабочих смен."""

import uuid
from datetime import date, time

from sqlalchemy.orm import Session, sessionmaker

from src.models import Shift
from src.repositories import EmployeeRepository, ShiftRepository
from src.validation import validate_shift


class ShiftService:
    """Бизнес-логика работы со сменами."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def add(
        self,
        employee_id: uuid.UUID,
        shift_date: date,
        start: time,
        end: time,
        description: str = "",
    ) -> Shift:
        """Создаёт смену после проверки корректности.

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

    def list_all(self, employee_id: uuid.UUID | None = None) -> list[Shift]:
        """Возвращает смены сотрудника (или все смены) по времени начала."""
        with self.session_factory() as session:
            return ShiftRepository(session).list_all(employee_id)
