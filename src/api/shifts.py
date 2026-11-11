"""API роутер для управления сменами."""
from uuid import UUID

from fastapi import APIRouter, Query

from src.api.dependencies import CurrentUser, RequireManagerOrAdmin
from src.container import paws_core
from src.dtos.requests import ShiftCreate
from src.dtos.responses import ShiftOut

router = APIRouter(prefix="/api/shifts", tags=["shifts"])


@router.get(
    "",
    response_model=list[ShiftOut],
    summary="Получить список смен",
    description="Возвращает список смен с возможностью фильтрации по ID сотрудника.",
    responses={401: {"description": "Необходима авторизация"}},
)
def get_shifts(
    _: CurrentUser,
    employee_id: UUID | None = Query(None, description="Фильтр по сотруднику"),
) -> list[ShiftOut]:
    """Возвращает историю смен."""
    return paws_core.list_shifts(employee_id=employee_id)


@router.post(
    "",
    response_model=ShiftOut,
    status_code=201,
    summary="Добавить смену",
    description="Создает новую смену для сотрудника. Доступно только для admin и manager.",
    responses={
        403: {"description": "Недостаточно прав"},
        404: {"description": "Сотрудник не найден"},
        409: {"description": "Конфликт (пересечение смен)"},
        422: {"description": "Ошибка формата данных"},
    },
)
def create_shift(shift_in: ShiftCreate, _: RequireManagerOrAdmin) -> ShiftOut:
    """Создает смену и возвращает сохраненный объект."""
    new_shift = paws_core.add_shift(
        employee_id=shift_in.employee_id,
        shift_date=shift_in.shift_date,
        start=shift_in.time_start,
        end=shift_in.time_end,
        description=shift_in.description or "",
    )
    return new_shift