"""API роутер для управления сотрудниками."""

from fastapi import APIRouter

from src.api.dependencies import CurrentUser, RequireManagerOrAdmin
from src.container import paws_core
from src.dtos.requests import EmployeeCreate
from src.dtos.responses import EmployeeOut

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get(
    "",
    response_model=list[EmployeeOut],
    summary="Получить список сотрудников",
    description="Возвращает полный список всех сотрудников компании.",
    responses={401: {"description": "Необходима авторизация"}},
)
def get_employees(_: CurrentUser) -> list[EmployeeOut]:
    """Отдает список всех зарегистрированных сотрудников."""
    return paws_core.list_employees()


@router.post(
    "",
    response_model=EmployeeOut,
    status_code=201,
    summary="Добавить сотрудника",
    description="Создает нового сотрудника. Доступно только для ролей admin и manager.",
    responses={
        403: {"description": "Недостаточно прав"},
        400: {"description": "Ошибка бизнес-валидации"},
        422: {"description": "Ошибка формата данных"},
    },
)
def create_employee(
    employee_in: EmployeeCreate, _: RequireManagerOrAdmin
) -> EmployeeOut:
    """Создает сотрудника и возвращает его данные."""
    new_emp = paws_core.add_employee(
        full_name=employee_in.full_name, position=employee_in.position
    )
    return new_emp
