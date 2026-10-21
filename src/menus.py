from enum import IntEnum
from typing import TypeVar

from src.app import PawsApp
from src.auth import AuthManager
from src.cli.handlers import (handle_add_employee, handle_add_shift,
                              handle_add_user, handle_list_employees,
                              handle_list_shifts, handle_list_users,
                              handle_login, handle_report,
                              handle_show_passwords)
from src.models import User

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

MenuChoiceT = TypeVar("MenuChoiceT", bound=IntEnum)


class AuthMenuChoice(IntEnum):
    """Пункты меню авторизации."""

    EXIT = 0
    LOGIN = 1
    SHOW_PASSWORDS = 2


class MainMenuChoice(IntEnum):
    """Пункты основного меню."""

    EXIT = 0
    ADD_EMPLOYEE = 1
    LIST_EMPLOYEES = 2
    ADD_SHIFT = 3
    LIST_SHIFTS = 4
    REPORT = 5
    ADD_USER = 6
    LIST_USERS = 7


def read_menu_choice(
    menu_text: str, choice_type: type[MenuChoiceT]
) -> MenuChoiceT | None:
    """Показывает меню и возвращает выбранный пункт или None при неверном вводе."""
    raw = input(menu_text).strip()
    try:
        return choice_type(int(raw))
    except ValueError:
        print("Неизвестный пункт меню, попробуйте снова")
        return None


def run_auth_menu(auth: AuthManager) -> User | None:
    """Меню авторизации: выполняется до успешного входа в систему."""
    while True:
        choice = read_menu_choice(AUTH_MENU, AuthMenuChoice)
        if choice is None:
            continue
        match choice:
            case AuthMenuChoice.LOGIN:
                user = handle_login(auth)
                if user is not None:
                    return user
            case AuthMenuChoice.SHOW_PASSWORDS:
                handle_show_passwords(auth)
            case AuthMenuChoice.EXIT:
                print("До свидания!")
                return None


def run_main_menu(app: PawsApp, auth: AuthManager) -> None:
    """Основное меню: доступно только после авторизации."""
    while True:
        choice = read_menu_choice(MAIN_MENU, MainMenuChoice)
        if choice is None:
            continue
        try:
            match choice:
                case MainMenuChoice.ADD_EMPLOYEE:
                    handle_add_employee(app)
                case MainMenuChoice.LIST_EMPLOYEES:
                    handle_list_employees(app)
                case MainMenuChoice.ADD_SHIFT:
                    handle_add_shift(app)
                case MainMenuChoice.LIST_SHIFTS:
                    handle_list_shifts(app)
                case MainMenuChoice.REPORT:
                    handle_report(app)
                case MainMenuChoice.ADD_USER:
                    handle_add_user(app, auth)
                case MainMenuChoice.LIST_USERS:
                    handle_list_users(app, auth)
                case MainMenuChoice.EXIT:
                    print("До свидания!")
                    return
        except (ValueError, OSError) as error:
            print(f"Ошибка: {error}")
