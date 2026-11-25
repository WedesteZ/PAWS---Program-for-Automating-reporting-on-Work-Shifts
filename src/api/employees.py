"""API роутер для управления сотрудниками."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user, require_manager_or_admin
from src.container import paws_core
from src.dtos.requests import EmployeeCreateRequest
from src.dtos.responses import EmployeeResponse

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get(
    "",
    summary="Получить список сотрудников",
    description="Возвращает полный список всех сотрудников компании.",
    dependencies=[Depends(get_current_user)],
    responses={401: {"description": "Необходима авторизация"}},
)
def get_employees() -> list[EmployeeResponse]:
    """Отдает список всех зарегистрированных сотрудников."""
    return [EmployeeResponse.model_validate(e) for e in paws_core.list_employees()]


@router.post(
    "",
    status_code=201,
    summary="Добавить сотрудника",
    description="Создает нового сотрудника. Доступно только для ролей admin и manager.",
    dependencies=[Depends(require_manager_or_admin)],
    responses={
        400: {"description": "Ошибка бизнес-валидации"},
        401: {"description": "Необходима авторизация"},
        403: {"description": "Недостаточно прав"},
        422: {"description": "Ошибка формата данных"},
    },
)
def create_employee(employee_in: EmployeeCreateRequest) -> EmployeeResponse:
    """Создает сотрудника и возвращает его данные."""
    new_emp = paws_core.add_employee(
        full_name=employee_in.full_name, position=employee_in.position
    )
    return EmployeeResponse.model_validate(new_emp)