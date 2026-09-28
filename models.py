import uuid
from dataclasses import dataclass, field
from datetime import date, time, datetime, timedelta
from enum import Enum


def new_id() -> str:
    """Генерирует уникальный идентификатор объекта (8 hex-символов)."""
    return uuid.uuid4().hex[:8]


class Role(Enum):
    """Роль пользователя в системе."""

    ADMIN = 'admin'
    MANAGER = 'manager'
    EMPLOYEE = 'employee'


@dataclass
class Employee:
    """Сотрудник: ФИО, должность и признак активности."""

    full_name: str
    position: str = ""
    active: bool = True
    id: str = field(default_factory=new_id)

    def deactivate(self) -> None:
        """Помечает сотрудника как уволенного (неактивного)."""
        self.active = False


@dataclass
class User:
    """Учётная запись для входа в систему, привязанная к сотруднику."""

    username: str
    password: str
    employee_id: str
    role: Role
    id: str = field(default_factory=new_id)


@dataclass
class Shift:
    """Рабочая смена сотрудника.

    Ночные смены (окончание раньше начала) считаются переходящими
    на следующие сутки.
    """

    employee_id: str
    shift_date: date
    time_start: time
    time_end: time
    description: str = ""
    status: str = "draft"
    id: str = field(default_factory=new_id)

    @property
    def calculate_duration(self) -> float:
        """Длительность смены в часах (округление до 2 знаков)."""
        start_dt = datetime.combine(self.shift_date, self.time_start)
        end_dt = datetime.combine(self.shift_date, self.time_end)
        if end_dt <= start_dt:
            end_dt = end_dt + timedelta(days=1)
        return round((end_dt - start_dt).total_seconds() / 3600, 2)
