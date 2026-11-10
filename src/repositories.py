import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Employee
from src.orm_models import EmployeeOrm


def employee_to_domain(row: EmployeeOrm) -> Employee:
    """Преобразует строку БД в объект Employee."""
    return Employee(
        full_name=row.full_name,
        position=row.position,
        department=row.department,
        hire_date=row.hire_date,
        phone=row.phone,
        email=row.email,
        active=row.is_active,
        id=row.id,
    )


class EmployeeRepository:
    """Доступ к сотрудникам в базе данных."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, employee: Employee) -> Employee:
        """Сохраняет сотрудника в сессии и возвращает его."""
        row = EmployeeOrm(
            id=employee.id,
            full_name=employee.full_name,
            position=employee.position,
            department=employee.department,
            hire_date=employee.hire_date,
            phone=employee.phone,
            email=employee.email,
            is_active=employee.active,
        )
        self.session.add(row)
        self.session.flush()
        return employee_to_domain(row)

    def get(self, employee_id: uuid.UUID) -> Employee | None:
        """Возвращает сотрудника по id или None."""
        row = self.session.get(EmployeeOrm, employee_id)
        return employee_to_domain(row) if row else None

    def list_all(self) -> list[Employee]:
        """Возвращает всех сотрудников, отсортированных по ФИО."""
        rows = self.session.scalars(
            select(EmployeeOrm).order_by(EmployeeOrm.full_name)
        )
        return [employee_to_domain(row) for row in rows]
