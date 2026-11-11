from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    username: str = Field(..., description="Логин", examples=["ivanov"])
    password: str = Field(..., description="Пароль", examples=["secret"])

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        """Очищает логин от лишних пробелов."""
        return v.strip()


class EmployeeCreate(BaseModel):
    full_name: str = Field(..., description="ФИО", examples=["Иванов Иван Иванович"])
    position: str = Field(..., description="Должность", examples=["Инженер"])

    @field_validator("full_name", "position")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        """Очищает строки от начальных и конечных пробелов."""
        return v.strip()


class ShiftCreate(BaseModel):
    employee_id: UUID = Field(..., description="ID сотрудника", examples=["123e4567-e89b-12d3-a456-426614174000"])
    shift_date: date = Field(..., description="Дата смены", examples=["2026-11-12"])
    time_start: time = Field(..., description="Начало смены", examples=["09:00:00"])
    time_end: time = Field(..., description="Конец смены", examples=["17:00:00"])
    description: str | None = Field(None, description="Описание смены", examples=["Дневная смена"])

    @model_validator(mode="after")
    def check_time(self) -> "ShiftCreate":
        if self.time_start >= self.time_end:
            raise ValueError("Время начала смены должно быть меньше времени окончания.")
        return self


class ReportRequest(BaseModel):
    date_from: date = Field(..., description="Начало периода", examples=["2026-11-01"])
    date_to: date = Field(..., description="Конец периода", examples=["2026-11-30"])
    employee_id: UUID | None = Field(None, description="ID сотрудника (опционально)", examples=["123e4567-e89b-12d3-a456-426614174000"])

    @model_validator(mode="after")
    def check_dates(self) -> "ReportRequest":
        if self.date_from > self.date_to:
            raise ValueError(
                "Дата начала (date_from) не может быть позже даты окончания (date_to)."
            )
        return self