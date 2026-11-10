from src.app import PawsApp
from src.auth import AuthManager
from src.cli.prompts import (
    read_date,
    read_employee_id,
    read_full_name,
    read_optional_employee_id,
    read_password,
    read_period,
    read_position,
    read_report_format,
    read_role,
    read_time,
    read_username,
)
from src.models import User

MAX_LOGIN_ATTEMPTS = 3


def handle_login(auth: AuthManager) -> User | None:
    """Запрашивает логин и пароль (до 3 попыток). Возвращает пользователя или None."""
    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        print(f"Авторизация (попытка {attempt} из {MAX_LOGIN_ATTEMPTS})")
        username = read_username("Логин: ")
        password = read_password("Пароль: ")
        try:
            user = auth.login(username, password)
            print(f"Вы вошли как {user.username} (роль={user.role.value})")
            return user
        except ValueError as error:
            print(f"Ошибка: {error}")
    print("Превышено число попыток авторизации")
    return None


def handle_add_employee(app: PawsApp) -> None:
    """Запрашивает данные и добавляет сотрудника."""
    name = read_full_name("ФИО сотрудника: ")
    position = read_position("Должность: ")
    employee = app.add_employee(name, position)
    print(f"Добавлен сотрудник: {employee.full_name}")


def handle_list_employees(app: PawsApp) -> None:
    """Выводит список сотрудников."""
    employees = app.list_employees()
    if not employees:
        print("Сотрудников нет")
    for number, e in enumerate(employees, start=1):
        print(f"  {number}. {e.full_name} ({e.position})")


def handle_add_shift(app: PawsApp) -> None:
    """Запрашивает данные и добавляет рабочую смену."""
    employee_id = read_employee_id("Номер сотрудника: ", app.list_employees())
    shift_date = read_date("Дата смены (ГГГГ-ММ-ДД): ")
    start = read_time("Начало (ЧЧ:ММ): ")
    end = read_time("Окончание (ЧЧ:ММ): ")
    description = input("Описание выполненных работ: ").strip()
    shift = app.add_shift(employee_id, shift_date, start, end, description)
    print(f"Смена добавлена ({shift.duration_hours} ч.)")


def handle_list_shifts(app: PawsApp) -> None:
    """Выводит смены выбранного сотрудника."""
    employee_id = read_employee_id("Номер сотрудника: ", app.list_employees())
    shifts = app.list_shifts(employee_id)
    if not shifts:
        print("Смен не найдено")
    for s in shifts:
        print(
            f"  {s.shift_date} {s.time_start}-{s.time_end} "
            f"({s.duration_hours} ч.) - {s.description}"
        )


def handle_report(app: PawsApp) -> None:
    """Формирует отчёт за период, выводит его и сохраняет в файл."""
    date_from, date_to = read_period()
    employee_id = read_optional_employee_id(
        "Номер сотрудника (пусто - по всем): ", app.list_employees()
    )
    report = app.generate_report(date_from, date_to, employee_id)
    print(report.text)
    fmt = read_report_format()
    filename = f"report.{fmt}"
    app.export_report(report, fmt, filename)
    print(f"Отчёт сохранён в файл: {filename}")


def handle_add_user(app: PawsApp, auth: AuthManager) -> None:
    """Запрашивает данные и добавляет пользователя системы."""
    username = read_username("Имя пользователя: ")
    password = read_password("Пароль: ")
    employee_id = read_employee_id("Номер сотрудника: ", app.list_employees())
    role = read_role("Роль")
    user = auth.add_user(username, password, employee_id, role)
    print(f"Пользователь добавлен: {user.username} (роль={user.role.value})")


def handle_list_users(app: PawsApp, auth: AuthManager) -> None:
    """Выводит список пользователей с ролями и привязанными сотрудниками."""
    users = auth.list_users()
    if not users:
        print("Пользователей нет")
    employees = {e.id: e for e in app.list_employees()}
    for u in users:
        employee = employees.get(u.employee_id)
        name = employee.full_name if employee else "?"
        print(f"  {u.username:15} роль={u.role.value:8} сотрудник={name}")
