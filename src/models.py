import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum


def new_id() -> str:
    """Генерирует уникальный идентификатор объекта (8 hex-символов)."""
    return uuid.uuid4().hex[:8]


class Role(Enum):
    """Роль пользователя в системе."""

    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


@dataclass
class Employee:
    """Сотрудник: ФИО, должность, контакты и признак активности."""

    full_name: str
    position: str = ""
    department: str | None = None
    hire_date: date = field(default_factory=date.today)
    phone: str | None = None
    email: str | None = None
    active: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def deactivate(self) -> None:
        """Помечает сотрудника как уволенного (неактивного)."""
        self.active = False


@dataclass
class User:
    """Учётная запись для входа в систему, привязанная к сотруднику."""

    username: str
    password_hash: str
    employee_id: uuid.UUID
    role: Role
    active: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def deactivate(self) -> None:
        """Блокирует учётную запись пользователя."""
        self.active = False


class ShiftStatus(Enum):
    """Статус рабочей смены."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CLOSED = "closed"


@dataclass
class CompletedWork:
    """Выполненная работа в рамках смены."""

    description: str
    work_date: date | None = None
    details: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Shift:
    """Рабочая смена сотрудника.

    Смена хранится как интервал: ночная смена заканчивается на следующие сутки.
    """

    employee_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    note: str | None = None
    status: ShiftStatus = ShiftStatus.DRAFT
    works: list[CompletedWork] = field(default_factory=list)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @classmethod
    def from_times(
        cls,
        employee_id: uuid.UUID,
        shift_date: date,
        start: time,
        end: time,
        description: str = "",
    ) -> "Shift":
        """Создаёт смену по дате и времени начала и окончания.

        Если окончание раньше начала, смена переходит на следующие сутки.
        """
        start_at = datetime.combine(shift_date, start)
        end_at = datetime.combine(shift_date, end)
        if end_at < start_at:
            end_at += timedelta(days=1)
        works = []
        if description:
            works.append(CompletedWork(description, work_date=shift_date))
        return cls(employee_id, start_at, end_at, works=works)

    @property
    def shift_date(self) -> date:
        """Дата начала смены."""
        return self.start_at.date()

    @property
    def time_start(self) -> time:
        """Время начала смены."""
        return self.start_at.time()

    @property
    def time_end(self) -> time:
        """Время окончания смены."""
        return self.end_at.time()

    @property
    def description(self) -> str:
        """Описание выполненных работ одной строкой."""
        return "; ".join(work.description for work in self.works)

    @property
    def duration_hours(self) -> float:
        """Длительность смены в часах (округление до 2 знаков)."""
        return round((self.end_at - self.start_at).total_seconds() / 3600, 2)


@dataclass(frozen=True)
class ReportRow:
    """Строка отчёта: одна смена одного сотрудника."""

    employee: str
    shift_date: date
    time_start: time
    time_end: time
    hours: float
    description: str


@dataclass(frozen=True)
class Report:
    """Готовый отчёт: текст для вывода, строки таблицы и итоги."""

    text: str
    rows: list[ReportRow]
    total_shifts: int
    total_hours: float
