from datetime import date, time
import re
from typing import Callable

from db import Storage
from models import Role, Shift


NAME_PATTERN = re.compile(r"^[А-Яа-яЁёA-Za-z\- ]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]{3,30}$")
REPORT_FORMATS = ("txt", "csv")


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
        errors.append("Логин может содержать только латинские буквы, "
                      "цифры и символы _ . - (3-30 символов)")

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


def validate_report_format(fmt: str) -> list[str]:
    """Проверяет формат отчёта. Возвращает список ошибок."""
    if fmt not in REPORT_FORMATS:
        return [f"Неизвестный формат '{fmt}', доступны: {'/'.join(REPORT_FORMATS)}"]
    return []



def validate_shift(shift: Shift, storage: Storage) -> list[str]:
    """Проверяет смену на корректность. Возвращает список ошибок."""
    errors = []

    if shift.employee_id not in storage.employees:
        errors.append("Сотрудник с таким ID не найден")

    if shift.time_start == shift.time_end:
        errors.append("Время начала и окончания смены совпадает")

    if shift.calculate_duration > 24:
        errors.append("Смена не может длиться больше 24 часов")

    for other in storage.shifts.values():
        if other.employee_id == shift.employee_id and other.shift_date == shift.shift_date:
            errors.append(
                f"У сотрудника уже есть смена {other.shift_date} "
                f"({other.time_start}-{other.time_end})"
            )

    return errors


def validate_user(username: str, password: str,
                  employee_id: str, storage: Storage) -> list[str]:
    """Проверяет данные нового пользователя. Возвращает список ошибок."""
    errors = validate_username(username)

    if username in storage.users:
        errors.append("Пользователь с таким именем уже существует")

    errors += validate_password(password)

    if employee_id not in storage.employees:
        errors.append("Сотрудник с таким ID не найден")
    elif any(u.employee_id == employee_id for u in storage.users.values()):
        errors.append("У этого сотрудника уже есть учётная запись "
                      "(один сотрудник — один пользователь)")

    return errors



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


def read_employee_id(prompt: str, storage: Storage,
                     allow_empty: bool = False) -> str | None:
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


def read_choice(prompt: str, choices: tuple[str, ...],
                default: str = "") -> str:
    """Запрашивает выбор одного из вариантов (пустой ввод — значение по умолчанию)."""
    while True:
        raw = input(f"{prompt} ({'/'.join(choices)}): ").strip().lower()
        if not raw and default:
            return default
        if raw in choices:
            return raw
        print(f"Ожидается одно из: {'/'.join(choices)}")


def read_validated(prompt: str, validator: Callable[[str], list[str]]) -> str:
    """Запрашивает значение до тех пор, пока validator не вернёт пустой список ошибок."""
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
