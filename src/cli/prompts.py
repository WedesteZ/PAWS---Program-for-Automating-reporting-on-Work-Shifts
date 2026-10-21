from collections.abc import Callable
from datetime import date, time

from src.db import Storage
from src.export import EXPORTERS
from src.models import Role
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


def read_employee_id(
    prompt: str, storage: Storage, allow_empty: bool = False
) -> str | None:
    """Запрашивает ID существующего сотрудника до корректного ввода.

    Перед вводом показывает список доступных сотрудников.
    Если allow_empty=True, пустой ввод возвращает None.
    """
    print("Доступные сотрудники:")
    if not storage.employees:
        print("  (список пуст)")
    for employee in storage.employees.values():
        print(f"  id={employee.id}: {employee.full_name} ({employee.position})")
    while True:
        raw = input(prompt).strip()
        if not raw and allow_empty:
            return None
        if raw in storage.employees:
            return raw
        print(f"Сотрудник с ID '{raw}' не найден, попробуйте снова")


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
