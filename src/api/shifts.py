from uuid import UUID
from fastapi import APIRouter, Depends, Query
from src.api.dependencies import CurrentUser, RequireManagerOrAdmin
from src.dtos.requests import ShiftCreate
from src.dtos.responses import ShiftOut
from src.main import paws_core

router = APIRouter(prefix="/api/shifts", tags=["shifts"])

@router.get(
    "",
    response_model=list[ShiftOut],
    summary="Получить список смен",
    description="Возвращает список смен. Возможна фильтрация по ID сотрудника.",
)
def get_shifts(
    _: CurrentUser,
    employee_id: UUID | None = Query(None, description="Фильтр по сотруднику")
):
    shifts = paws_core.list_shifts(employee_id=employee_id)
    return shifts

@router.post(
    "",
    response_model=ShiftOut,
    status_code=201,
    summary="Добавить смену",
    description="Создает новую смену для сотрудника. Доступно только для admin и manager.",
    responses={403: {"description": "Недостаточно прав"}, 409: {"description": "Конфликт (пересечение смен)"}},
)
def create_shift(shift_in: ShiftCreate, _: RequireManagerOrAdmin):
    paws_core.add_shift(
        employee_id=shift_in.employee_id,
        shift_date=shift_in.shift_date,
        start=shift_in.time_start,
        end=shift_in.time_end,
        description=shift_in.description or ""
    )
    # Получаем последнюю добавленную смену
    shifts = paws_core.list_shifts(employee_id=shift_in.employee_id)
    return shifts[-1]