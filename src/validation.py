import re

from src.db import Storage
from src.models import Shift

NAME_PATTERN = re.compile(r"^[А-Яа-яЁёA-Za-z\- ]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]{3,30}$")


def validate_full_name(full_name: str) -> list[str]:
    """Проверяет ФИО. Возвращает список ошибок."""
    errors = []

    if not full_name:
        errors.append("ФИО не может быть пустым")

    if len(full_name.split()) < 2:
        errors.append("Укажите фамилию и имя (минимум два слова)")

    if full_name and not NAME_PATTERN.fullmatch(full_name):
        errors.append("ФИО может содержать только буквы, пробелы и дефисы")

    return errors


def validate_position(position: str) -> list[str]:
    """Проверяет должность. Возвращает список ошибок."""
    errors = []

    if not position:
        errors.append("Должность не может быть пустой")

    if len(position) > 50:
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

    if len(password) < 4:
        errors.append("Пароль должен содержать минимум 4 символа")

    if len(password) > 64:
        errors.append("Пароль не может быть длиннее 64 символов")

    return errors


def validate_shift(shift: Shift, storage: Storage) -> list[str]:
    """Проверяет смену на корректность. Возвращает список ошибок."""
    errors = []

    if shift.employee_id not in storage.employees:
        errors.append("Сотрудник с таким ID не найден")

    if shift.time_start == shift.time_end:
        errors.append("Время начала и окончания смены совпадает")

    if shift.duration_hours > 24:
        errors.append("Смена не может длиться больше 24 часов")

    for other in storage.shifts.values():
        if (
            other.employee_id == shift.employee_id
            and other.shift_date == shift.shift_date
        ):
            errors.append(
                f"У сотрудника уже есть смена {other.shift_date} "
                f"({other.time_start}-{other.time_end})"
            )

    return errors


def validate_user(
    username: str, password: str, employee_id: str, storage: Storage
) -> list[str]:
    """Проверяет данные нового пользователя. Возвращает список ошибок."""
    errors = validate_username(username)

    if username in storage.users:
        errors.append("Пользователь с таким именем уже существует")

    errors += validate_password(password)

    if employee_id not in storage.employees:
        errors.append("Сотрудник с таким ID не найден")
    elif any(u.employee_id == employee_id for u in storage.users.values()):
        errors.append(
            "У этого сотрудника уже есть учётная запись "
            "(один сотрудник — один пользователь)"
        )

    return errors
