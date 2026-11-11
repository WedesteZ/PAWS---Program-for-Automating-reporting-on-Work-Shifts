from datetime import date, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=30, description="Логин пользователя", examples=["admin"]
    )
    password: str = Field(
        ..., min_length=4, max_length=64, description="Пароль", examples=["admin123"]
    )


class EmployeeCreate(BaseModel):
    full_name: str = Field(
        ..., min_length=2, max_length=150, description="ФИО сотрудника", examples=["Иванов Иван Иванович"]
    )
    position: str = Field(
        ..., min_length=1, max_length=50, description="Должность", examples=["Охранник"]
    )


class ShiftCreate(BaseModel):
    employee_id: UUID = Field(..., description="ID сотрудника")
    shift_date: date = Field(..., description="Дата смены")
    time_start: time = Field(..., description="Время начала смены (ЧЧ:ММ)")
    time_end: time = Field(..., description="Время окончания смены (ЧЧ:ММ)")
    description: str | None = Field(
        None, max_length=255, description="Заметки", examples=["Ночная смена"]
    )

    @model_validator(mode="after")
    def check_time(self) -> "ShiftCreate":
        if self.time_start == self.time_end:
            raise ValueError("Время начала и окончания смены не может совпадать.")
        return self


class ReportRequest(BaseModel):
    date_from: date = Field(..., description="Начало периода")
    date_to: date = Field(..., description="Конец периода")
    employee_id: UUID | None = Field(None, description="Фильтр по ID сотрудника")
    export_format: Literal["pdf", "xlsx"] | None = Field(
        None, description="Формат экспорта (если нужен файл)"
    )

    @model_validator(mode="after")
    def check_dates(self) -> "ReportRequest":
        if self.date_from > self.date_to:
            raise ValueError("Дата начала (date_from) не может быть позже даты окончания (date_to).")
        return self