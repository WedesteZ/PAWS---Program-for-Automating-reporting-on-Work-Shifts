import re
import uuid

from src.models import Shift
from src.repositories import EmployeeRepository, ShiftRepository, UserRepository

NAME_PATTERN = re.compile(r"^[А-Яа-яЁёA-Za-z\- ]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]{3,30}$")


def validate_full_name(full_name: str) -> list[str]:
    """Проверяет ФИО. Возвращает список ошибок."""
    errors = []

    if not full_name:
        errors.append("ФИО не может быть пустым")

    if full_name and len(full_name.split()) < 2:
        errors.append("Укажите фамилию и имя (минимум два слова)")

    if full_name and len(full_name) > 150:
        errors.append("ФИО не может быть длиннее 150 символов")

    if full_name and not NAME_PATTERN.fullmatch(full_name):
        errors.append("ФИО может содержать только буквы, пробелы и дефисы")

    return errors


def validate_position(position: str) -> list[str]:
    """Проверяет должность. Возвращает список ошибок."""
    errors = []

    if not position:
        errors.append("Должность не может быть пустой")

    if position and len(position) > 50:
        errors.append("Должность не может быть длиннее 50 символов")

    return errors


def validate_username(username: str) -> list[str]:
    """Проверяет имя пользователя. Возвращает список ошибок."""
    errors = []

    if not username:
        errors.append("Имя пользователя не может быть пустым")

    if username and not USERNAME_PATTERN.fullmatch(username):
        errors.append(
            "Логин может содержать только латинские буквы, "
            "цифры и символы _ . - (3-30 символов)"
        )

    return errors


def validate_password(password: str) -> list[str]:
    """Проверяет пароль. Возвращает список ошибок."""
    errors = []

    if not password:
        errors.append("Пароль не может быть пустым")

    if password and len(password) < 4:
        errors.append("Пароль должен содержать минимум 4 символа")

    if password and len(password) > 64:
        errors.append("Пароль не может быть длиннее 64 символов")

    return errors


def validate_shift(
    shift: Shift, employees: EmployeeRepository, shifts: ShiftRepository
) -> list[str]:
    """Проверяет смену на корректность. Возвращает список ошибок."""
    errors = []

    if employees.get(shift.employee_id) is None:
        errors.append("Сотрудник с таким ID не найден")

    if shift.start_at == shift.end_at:
        errors.append("Время начала и окончания смены совпадает")

    if shift.duration_hours > 24:
        errors.append("Смена не может длиться больше 24 часов")

    for other in shifts.find_overlapping(
        shift.employee_id, shift.start_at, shift.end_at
    ):
        errors.append(
            f"Смена пересекается с другой сменой сотрудника: "
            f"{other.start_at:%Y-%m-%d %H:%M} - {other.end_at:%Y-%m-%d %H:%M}"
        )

    return errors


def validate_user(
    username: str,
    password: str,
    employee_id: uuid.UUID,
    users: UserRepository,
    employees: EmployeeRepository,
) -> list[str]:
    """Проверяет данные нового пользователя. Возвращает список ошибок."""
    errors = validate_username(username)

    if users.get_by_username(username) is not None:
        errors.append("Пользователь с таким именем уже существует")

    errors += validate_password(password)

    if employees.get(employee_id) is None:
        errors.append("Сотрудник с таким ID не найден")
    elif users.get_by_employee_id(employee_id) is not None:
        errors.append(
            "У этого сотрудника уже есть учётная запись "
            "(один сотрудник — один пользователь)"
        )

    return errors
