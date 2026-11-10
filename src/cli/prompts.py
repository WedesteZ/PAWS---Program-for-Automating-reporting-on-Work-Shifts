import uuid
from collections.abc import Callable
from datetime import date, time

from src.export import EXPORTERS
from src.models import Employee, Role
from src.validation import (
    validate_full_name,
    validate_password,
    validate_position,
    validate_username,
)

REPORT_FORMATS = tuple(EXPORTERS)


def read_nonempty(prompt: str) -> str:
    """Запрашивает непустую строку до корректного ввода."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не может быть пустым, попробуйте снова")


def read_date(prompt: str) -> date:
    """Запрашивает дату в формате ГГГГ-ММ-ДД до корректного ввода."""
    while True:
        raw = input(prompt).strip()
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print(f"Некорректная дата '{raw}', ожидается формат ГГГГ-ММ-ДД")


def read_time(prompt: str) -> time:
    """Запрашивает время в формате ЧЧ:ММ до корректного ввода."""
    while True:
        raw = input(prompt).strip()
        try:
            return time.fromisoformat(raw)
        except ValueError:
            print(f"Некорректное время '{raw}', ожидается формат ЧЧ:ММ")


def read_period() -> tuple[date, date]:
    """Запрашивает период дат и проверяет, что начало не позже конца."""
    while True:
        date_from = read_date("Период с (ГГГГ-ММ-ДД): ")
        date_to = read_date("Период по (ГГГГ-ММ-ДД): ")
        if date_from <= date_to:
            return date_from, date_to
        print("Начало периода не может быть позже его окончания, попробуйте снова")


def print_employees(employees: list[Employee]) -> None:
    """Выводит нумерованный список сотрудников."""
    print("Доступные сотрудники:")
    if not employees:
        print("  (список пуст)")
    for number, employee in enumerate(employees, start=1):
        print(f"  {number}. {employee.full_name} ({employee.position})")


def read_optional_employee_id(
    prompt: str, employees: list[Employee]
) -> uuid.UUID | None:
    """Запрашивает номер сотрудника из списка (пустой ввод — None)."""
    print_employees(employees)
    while True:
        raw = input(prompt).strip()
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(employees):
            return employees[int(raw) - 1].id
        print(f"Нет сотрудника с номером '{raw}', попробуйте снова")


def read_employee_id(prompt: str, employees: list[Employee]) -> uuid.UUID:
    """Запрашивает номер сотрудника из списка до корректного ввода.

    Raises:
        ValueError: если список сотрудников пуст.
    """
    if not employees:
        raise ValueError("Список сотрудников пуст, сначала добавьте сотрудника")
    print_employees(employees)
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(employees):
            return employees[int(raw) - 1].id
        print(f"Нет сотрудника с номером '{raw}', попробуйте снова")


def read_role(prompt: str) -> Role:
    """Запрашивает роль до корректного ввода."""
    roles = "/".join(r.value for r in Role)
    while True:
        raw = input(f"{prompt} ({roles}): ").strip()
        try:
            return Role(raw)
        except ValueError:
            print(f"Неизвестная роль '{raw}', доступны: {roles}")


def read_choice(prompt: str, choices: tuple[str, ...], default: str = "") -> str:
    """Запрашивает выбор одного из вариантов (пустой ввод — значение по умолчанию)."""
    while True:
        raw = input(f"{prompt} ({'/'.join(choices)}): ").strip().lower()
        if not raw and default:
            return default
        if raw in choices:
            return raw
        print(f"Ожидается одно из: {'/'.join(choices)}")


def read_validated(prompt: str, validator: Callable[[str], list[str]]) -> str:
    """Запрашивает значение, пока validator не вернёт пустой список ошибок."""
    while True:
        value = input(prompt).strip()
        errors = validator(value)
        if not errors:
            return value
        print("; ".join(errors))


def read_full_name(prompt: str) -> str:
    """Запрашивает ФИО (минимум фамилия и имя) до корректного ввода."""
    return read_validated(prompt, validate_full_name)


def read_position(prompt: str) -> str:
    """Запрашивает должность до корректного ввода."""
    return read_validated(prompt, validate_position)


def read_username(prompt: str) -> str:
    """Запрашивает имя пользователя до корректного ввода."""
    return read_validated(prompt, validate_username)


def read_password(prompt: str) -> str:
    """Запрашивает пароль до корректного ввода."""
    return read_validated(prompt, validate_password)


def read_report_format() -> str:
    """Запрашивает формат отчёта (txt/csv, пустой ввод — txt) до корректного ввода."""
    return read_choice("Формат сохранения", REPORT_FORMATS, default="txt")
