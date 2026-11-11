from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    username: str = Field(..., description="Логин пользователя")
    role: str = Field(..., description="Роль пользователя (admin, manager, employee)")


class EmployeeOut(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор")
    full_name: str = Field(..., description="ФИО")
    position: str = Field(..., description="Должность")


class ShiftOut(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор смены")
    employee_id: UUID = Field(..., description="ID сотрудника")
    shift_date: date = Field(..., description="Дата смены")
    time_start: time = Field(..., description="Начало")
    time_end: time = Field(..., description="Конец")
    description: str | None = Field(None, description="Описание")


class ReportRowOut(BaseModel):
    shift_date: date = Field(..., description="Дата")
    employee: str = Field(..., description="ФИО сотрудника")
    time_start: time = Field(..., description="Начало смены")
    time_end: time = Field(..., description="Конец смены")
    hours: float = Field(..., description="Длительность (часы)")
    description: str = Field(..., description="Заметки")


class ReportOut(BaseModel):
    text: str = Field(..., description="Заголовок/описание отчета")
    date_from: date = Field(..., description="Начало периода")
    date_to: date = Field(..., description="Конец периода")
    total_hours: float = Field(..., description="Итого часов за период")
    rows: list[ReportRowOut] = Field(default_factory=list, description="Строки отчета")