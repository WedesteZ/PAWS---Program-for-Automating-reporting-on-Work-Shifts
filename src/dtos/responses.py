from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    """Модель ответа с данными авторизованного пользователя."""

    model_config = ConfigDict(from_attributes=True)
    username: str = Field(..., description="Логин пользователя", examples=["ivanov"])
    role: str = Field(..., description="Роль пользователя", examples=["admin"])


class EmployeeOut(BaseModel):
    """Модель ответа с публичными данными сотрудника."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID = Field(
        ...,
        description="Уникальный идентификатор",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    full_name: str = Field(..., description="ФИО", examples=["Иванов Иван Иванович"])
    position: str = Field(..., description="Должность", examples=["Инженер"])


class ShiftOut(BaseModel):
    """Модель ответа с информацией о рабочей смене."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID = Field(
        ...,
        description="Уникальный идентификатор смены",
        examples=["987fcdeb-51a2-43d7-9012-345678901234"],
    )
    employee_id: UUID = Field(
        ...,
        description="ID сотрудника",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    shift_date: date = Field(..., description="Дата смены", examples=["2026-11-12"])
    time_start: time = Field(..., description="Начало", examples=["09:00:00"])
    time_end: time = Field(..., description="Конец", examples=["17:00:00"])
    description: str | None = Field(
        None, description="Описание", examples=["Дневная смена"]
    )


class ReportRowOut(BaseModel):
    """Модель строки отчета по конкретной смене."""

    model_config = ConfigDict(from_attributes=True)
    shift_date: date = Field(..., description="Дата", examples=["2026-11-12"])
    employee: str = Field(
        ..., description="ФИО сотрудника", examples=["Иванов Иван Иванович"]
    )
    time_start: time = Field(..., description="Начало смены", examples=["09:00:00"])
    time_end: time = Field(..., description="Конец смены", examples=["17:00:00"])
    hours: float = Field(..., description="Длительность (часы)", examples=[8.0])
    description: str | None = Field(
        None, description="Заметки", examples=["Дневная смена"]
    )


class ReportOut(BaseModel):
    """Модель ответа с агрегированным отчетом за период."""

    model_config = ConfigDict(from_attributes=True)
    title: str = Field(
        ..., description="Заголовок отчета", examples=["Отчет по отработанному времени"]
    )
    period: str = Field(..., description="Период", examples=["2026-11-01 - 2026-11-30"])
    total_shifts: int = Field(..., description="Всего смен", examples=[20])
    total_hours: float = Field(
        ..., description="Итого часов за период", examples=[160.0]
    )
    rows: list[ReportRowOut] = Field(default_factory=list, description="Строки отчета")
