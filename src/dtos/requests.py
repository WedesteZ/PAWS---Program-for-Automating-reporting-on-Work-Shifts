from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    """Модель запроса для авторизации пользователя."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Логин пользователя",
        examples=["admin"],
    )
    password: str = Field(
        ..., min_length=4, max_length=64, description="Пароль", examples=["admin123"]
    )

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        """Очищает логин от лишних пробелов."""
        return v.strip()


class EmployeeCreate(BaseModel):
    """Модель запроса для создания нового сотрудника."""

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="ФИО сотрудника",
        examples=["Иванов Иван Иванович"],
    )
    position: str = Field(
        ..., min_length=1, max_length=50, description="Должность", examples=["Охранник"]
    )

    @field_validator("full_name", "position")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        """Очищает строки от начальных и конечных пробелов."""
        return v.strip()


class ShiftCreate(BaseModel):
    """Модель запроса для добавления новой смены."""

    employee_id: UUID = Field(
        ...,
        description="ID сотрудника",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    shift_date: date = Field(..., description="Дата смены", examples=["2026-11-12"])
    time_start: time = Field(
        ..., description="Время начала смены (ЧЧ:ММ)", examples=["09:00:00"]
    )
    time_end: time = Field(
        ..., description="Время окончания смены (ЧЧ:ММ)", examples=["17:00:00"]
    )
    description: str | None = Field(
        None, max_length=255, description="Заметки", examples=["Ночная смена"]
    )

    @model_validator(mode="after")
    def check_time(self) -> "ShiftCreate":
        """Проверяет, что время начала и окончания смены не совпадает."""
        if self.time_start == self.time_end:
            raise ValueError("Время начала и окончания смены не может совпадать.")
        return self


class ReportRequest(BaseModel):
    """Модель запроса для генерации отчета по сменам."""

    date_from: date = Field(..., description="Начало периода", examples=["2026-11-01"])
    date_to: date = Field(..., description="Конец периода", examples=["2026-11-30"])
    employee_id: UUID | None = Field(
        None,
        description="Фильтр по ID сотрудника",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    @model_validator(mode="after")
    def check_dates(self) -> "ReportRequest":
        """Проверяет, что дата начала периода не превышает дату окончания."""
        if self.date_from > self.date_to:
            raise ValueError(
                "Дата начала (date_from) не может быть позже даты окончания (date_to)."
            )
        return self
