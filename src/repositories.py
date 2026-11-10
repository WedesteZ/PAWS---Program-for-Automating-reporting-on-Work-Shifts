import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Employee, Role, User
from src.orm_models import EmployeeOrm, UserOrm


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


def user_to_domain(row: UserOrm) -> User:
    """Преобразует строку БД в объект User."""
    return User(
        username=row.login,
        password_hash=row.password_hash,
        employee_id=row.employee_id,
        role=Role(row.user_role),
        id=row.id,
    )


class UserRepository:
    """Доступ к учётным записям пользователей в базе данных."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, user: User) -> User:
        """Сохраняет пользователя в сессии и возвращает его."""
        row = UserOrm(
            id=user.id,
            login=user.username,
            password_hash=user.password_hash,
            user_role=user.role.value,
            employee_id=user.employee_id,
        )
        self.session.add(row)
        self.session.flush()
        return user_to_domain(row)

    def get_by_username(self, username: str) -> User | None:
        """Возвращает пользователя по логину или None."""
        row = self.session.scalar(select(UserOrm).where(UserOrm.login == username))
        return user_to_domain(row) if row else None

    def get_by_employee_id(self, employee_id: uuid.UUID) -> User | None:
        """Возвращает учётную запись сотрудника или None."""
        row = self.session.scalar(
            select(UserOrm).where(UserOrm.employee_id == employee_id)
        )
        return user_to_domain(row) if row else None

    def list_all(self) -> list[User]:
        """Возвращает всех пользователей, отсортированных по логину."""
        rows = self.session.scalars(select(UserOrm).order_by(UserOrm.login))
        return [user_to_domain(row) for row in rows]
