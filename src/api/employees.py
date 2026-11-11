from fastapi import APIRouter, Depends
from src.api.dependencies import CurrentUser, RequireManagerOrAdmin
from src.dtos.requests import EmployeeCreate
from src.dtos.responses import EmployeeOut
# Предполагается импорт paws_core из модуля инициализации приложения
from src.main import paws_core

router = APIRouter(prefix="/api/employees", tags=["employees"])

@router.get(
    "",
    response_model=list[EmployeeOut],
    summary="Получить список сотрудников",
    description="Возвращает полный список всех сотрудников компании.",
)
def get_employees(_: CurrentUser):
    employees = paws_core.list_employees()
    return [{"id": emp.id, "full_name": emp.full_name, "position": emp.position} for emp in employees]

@router.post(
    "",
    response_model=EmployeeOut,
    status_code=201,
    summary="Добавить сотрудника",
    description="Создает нового сотрудника. Доступно только для ролей admin и manager.",
    responses={403: {"description": "Недостаточно прав"}, 400: {"description": "Ошибка валидации"}},
)
def create_employee(employee_in: EmployeeCreate, _: RequireManagerOrAdmin):
    # Если paws_core выбрасывает ValueError, наш будущий глобальный обработчик поймает его и отдаст 400
    paws_core.add_employee(full_name=employee_in.full_name, position=employee_in.position)
    # Ищем добавленного сотрудника, чтобы вернуть его (или paws_core должен возвращать объект)
    emps = paws_core.list_employees()
    new_emp = next(e for e in emps if e.full_name == employee_in.full_name)
    return {"id": new_emp.id, "full_name": new_emp.full_name, "position": new_emp.position}