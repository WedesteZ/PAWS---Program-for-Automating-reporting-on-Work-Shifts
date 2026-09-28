from datetime import date, time

from app import PawsApp
from auth import AuthManager
from models import Role, User
from validation import (read_date, read_employee_id, read_full_name,
                        read_password, read_period, read_position,
                        read_report_format, read_role, read_time,
                        read_username)

MAX_LOGIN_ATTEMPTS = 3


def seed_demo_data(app: PawsApp, auth: AuthManager) -> None:
    """Загружает демо-данные: 5 сотрудников, каждому — пользователь со своей ролью."""
    demo = [
        ("Иванов Иван Иванович", "Оператор", "ivanov", "admin123", Role.ADMIN),
        ("Петров Пётр Петрович", "Оператор", "petrov", "manager123", Role.MANAGER),
        ("Сидорова Анна Сергеевна", "Старший оператор", "sidorova", "worker123", Role.EMPLOYEE),
        ("Кузнецов Дмитрий Алексеевич", "Кладовщик", "kuznetsov", "store123", Role.EMPLOYEE),
        ("Смирнова Ольга Викторовна", "Бухгалтер", "smirnova", "budget123", Role.MANAGER),
    ]
    for full_name, position, username, password, role in demo:
        employee = app.add_employee(full_name, position)
        auth.add_user(username, password, employee.id, role)

    app.add_shift(app.list_employees()[0].id, date.today(),
                  time(8, 0), time(20, 0), "Приём заказов")
    app.add_shift(app.list_employees()[1].id, date.today(),
                  time(20, 0), time(8, 0), "Ночная смена, склад")
    print(f"Демо-данные загружены: {len(demo)} сотрудников, {len(demo)} пользователей")


AUTH_MENU = """
==== PAWS - авторизация ====
1. Авторизоваться
2. Вывод паролей пользователей
0. Выход
Выберите пункт: """

MAIN_MENU = """
==== PAWS - учёт рабочих смен ====
1. Добавить сотрудника
2. Показать список сотрудников
3. Добавить смену
4. Показать смены сотрудника
5. Сформировать и сохранить отчёт
6. Добавить пользователя
7. Показать список пользователей
0. Выход
Выберите пункт: """


def show_user_passwords(auth: AuthManager) -> None:
    """Выводит список пользователей с их паролями и ролями."""
    users = auth.list_users()
    if not users:
        print("Пользователей нет")
    for u in users:
        print(f"  {u.username:12} пароль={u.password:12} роль={u.role.value}")


def authorize(auth: AuthManager) -> User | None:
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


def run_auth_menu(app: PawsApp, auth: AuthManager) -> User | None:
    """Меню авторизации: выполняется до успешного входа в систему."""
    while True:
        choice = input(AUTH_MENU).strip()
        try:
            match choice:
                case "1":
                    user = authorize(auth)
                    if user is not None:
                        return user

                case "2":
                    show_user_passwords(auth)

                case "0":
                    print("До свидания!")
                    return None

                case "_":
                    print("Неизвестный пункт меню, попробуйте снова")

        except Exception as error:
            print(f"Ошибка: {error}")


def run_main_menu(app: PawsApp, auth: AuthManager) -> None:
    """Основное меню: доступно только после авторизации."""
    while True:
        choice = input(MAIN_MENU).strip()
        try:
            match choice:
                case "1":
                    name = read_full_name("ФИО сотрудника: ")
                    position = read_position("Должность: ")
                    employee = app.add_employee(name, position)
                    print(f"Добавлен сотрудник: {employee.full_name} (id={employee.id})")

                case "2":
                    for e in app.list_employees():
                        print(f"  id={e.id}: {e.full_name} ({e.position})")

                case "3":
                    employee_id = read_employee_id("ID сотрудника: ", app.storage)
                    shift_date = read_date("Дата смены (ГГГГ-ММ-ДД): ")
                    start = read_time("Начало (ЧЧ:ММ): ")
                    end = read_time("Окончание (ЧЧ:ММ): ")
                    description = input("Описание выполненных работ: ").strip()
                    shift = app.add_shift(employee_id, shift_date, start, end, description)
                    print(f"Смена добавлена (id={shift.id}, "
                          f"{shift.calculate_duration} ч.)")

                case "4":
                    employee_id = read_employee_id("ID сотрудника: ", app.storage)
                    shifts = app.list_shifts(employee_id)
                    if not shifts:
                        print("Смен не найдено")
                    for s in shifts:
                        print(f"  {s.shift_date} {s.time_start}-{s.time_end} "
                              f"({s.calculate_duration} ч.) - {s.description}")

                case "5":
                    date_from, date_to = read_period()
                    employee_id = read_employee_id(
                        "ID сотрудника (пусто - по всем): ", app.storage, allow_empty=True)
                    report = app.generate_report(date_from, date_to, employee_id)
                    print(report["text"])
                    fmt = read_report_format()
                    filename = f"report.{fmt}"
                    app.export_report(report, fmt, filename)
                    print(f"Отчёт сохранён в файл: {filename}")

                case "6":
                    username = read_username("Имя пользователя: ")
                    password = read_password("Пароль: ")
                    employee_id = read_employee_id("ID сотрудника: ", app.storage)
                    role = read_role("Роль")
                    user = auth.add_user(username, password, employee_id, role)
                    print(f"Пользователь добавлен: {user.username} "
                          f"(роль={user.role.value}, id={user.id})")

                case "7":
                    users = auth.list_users()
                    if not users:
                        print("Пользователей нет")
                    for u in users:
                        employee = app.storage.employees.get(u.employee_id)
                        name = employee.full_name if employee else "?"
                        print(f"  {u.username:15} роль={u.role.value:8} "
                              f"сотрудник={name} (id={u.id})")

                case "0":
                    print("До свидания!")
                    return

                case "_":
                    print("Неизвестный пункт меню, попробуйте снова")

        except Exception as error:
            print(f"Ошибка: {error}")


def main() -> None:
    """Главная функция: сначала меню авторизации, затем основное меню."""
    app = PawsApp()
    auth = AuthManager(app.storage)
    seed_demo_data(app, auth)

    user = run_auth_menu(app, auth)
    if user is not None:
        run_main_menu(app, auth)


if __name__ == "__main__":
    main()