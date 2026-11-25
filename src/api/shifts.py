"""API роутер для управления сменами."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_current_user, require_manager_or_admin
from src.container import paws_core
from src.dtos.requests import ShiftCreateRequest
from src.dtos.responses import ShiftResponse

router = APIRouter(prefix="/api/shifts", tags=["shifts"])


@router.get(
    "",
    summary="Получить список смен",
    description="Возвращает список смен с возможностью фильтрации по ID сотрудника.",
    dependencies=[Depends(get_current_user)],
    responses={401: {"description": "Необходима авторизация"}},
)
def get_shifts(
    employee_id: Annotated[UUID | None, Query(description="Фильтр")] = None,
) -> list[ShiftResponse]:
    """Возвращает историю смен."""
    shifts = paws_core.list_shifts(employee_id=employee_id)
    return [
        ShiftResponse(
            id=s.id,
            employee_id=s.employee_id,
            shift_date=s.shift_date,
            time_start=s.time_start,
            time_end=s.time_end,
            description=s.description,
        )
        for s in shifts
    ]


@router.post(
    "",
    status_code=201,
    summary="Добавить смену",
    description="Создает смену. Доступно только для admin и manager.",
    dependencies=[Depends(require_manager_or_admin)],
    responses={
        401: {"description": "Необходима авторизация"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Сотрудник не найден"},
        409: {"description": "Конфликт (пересечение смен)"},
        422: {"description": "Ошибка формата данных"},
    },
)
def create_shift(shift_in: ShiftCreateRequest) -> ShiftResponse:
    """Создает смену и возвращает сохраненный объект."""
    s = paws_core.add_shift(
        employee_id=shift_in.employee_id,
        shift_date=shift_in.shift_date,
        start=shift_in.time_start,
        end=shift_in.time_end,
        description=shift_in.description or "",
    )
    return ShiftResponse(
        id=s.id,
        employee_id=s.employee_id,
        shift_date=s.shift_date,
        time_start=s.time_start,
        time_end=s.time_end,
        description=s.description,
    )