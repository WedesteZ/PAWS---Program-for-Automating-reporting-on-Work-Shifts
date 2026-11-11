import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src import CompletedWork, Employee, Role, Shift, ShiftStatus, User
from src import CompletedWorkOrm, EmployeeOrm, ShiftOrm, UserOrm


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


def work_to_domain(row: CompletedWorkOrm) -> CompletedWork:
    """Преобразует строку БД в объект CompletedWork."""
    return CompletedWork(
        description=row.description,
        work_date=row.work_date,
        details=row.details,
        id=row.id,
    )


def shift_to_domain(row: ShiftOrm) -> Shift:
    """Преобразует строку БД в объект Shift вместе с выполненными работами."""
    return Shift(
        employee_id=row.employee_id,
        start_at=row.start_at,
        end_at=row.end_at,
        note=row.note,
        status=ShiftStatus(row.status),
        works=[work_to_domain(work) for work in row.works],
        id=row.id,
    )


class ShiftRepository:
    """Доступ к сменам и выполненным работам в базе данных."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, shift: Shift) -> Shift:
        """Сохраняет смену вместе с работами и возвращает её."""
        row = ShiftOrm(
            id=shift.id,
            employee_id=shift.employee_id,
            start_at=shift.start_at,
            end_at=shift.end_at,
            status=shift.status.value,
            note=shift.note,
            works=[
                CompletedWorkOrm(
                    id=work.id,
                    description=work.description,
                    work_date=work.work_date,
                    details=work.details,
                )
                for work in shift.works
            ],
        )
        self.session.add(row)
        self.session.flush()
        return shift_to_domain(row)

    def list_all(self, employee_id: uuid.UUID | None = None) -> list[Shift]:
        """Возвращает смены (всех или одного сотрудника) по времени начала."""
        query = (
            select(ShiftOrm)
            .options(selectinload(ShiftOrm.works))
            .order_by(ShiftOrm.start_at)
        )
        if employee_id is not None:
            query = query.where(ShiftOrm.employee_id == employee_id)
        return [shift_to_domain(row) for row in self.session.scalars(query)]

    def list_between(
        self,
        date_from: date,
        date_to: date,
        employee_id: uuid.UUID | None = None,
    ) -> list[Shift]:
        """Возвращает смены, начавшиеся в периоде (границы включаются)."""
        period_start = datetime.combine(date_from, time.min)
        period_end = datetime.combine(date_to, time.min) + timedelta(days=1)
        query = (
            select(ShiftOrm)
            .options(selectinload(ShiftOrm.works))
            .where(ShiftOrm.start_at >= period_start, ShiftOrm.start_at < period_end)
            .order_by(ShiftOrm.start_at)
        )
        if employee_id is not None:
            query = query.where(ShiftOrm.employee_id == employee_id)
        return [shift_to_domain(row) for row in self.session.scalars(query)]

    def find_overlapping(
        self, employee_id: uuid.UUID, start_at: datetime, end_at: datetime
    ) -> list[Shift]:
        """Возвращает смены сотрудника, пересекающиеся с заданным интервалом."""
        query = (
            select(ShiftOrm)
            .options(selectinload(ShiftOrm.works))
            .where(
                ShiftOrm.employee_id == employee_id,
                ShiftOrm.start_at < end_at,
                ShiftOrm.end_at > start_at,
            )
        )
        return [shift_to_domain(row) for row in self.session.scalars(query)]
