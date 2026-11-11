import uuid
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from src.validation import (
    validate_full_name,
    validate_password,
    validate_position,
    validate_shift,
    validate_user,
    validate_username,
)


@pytest.mark.parametrize("name", [
    "Иванов Иван",
    "Иван " + "А" * 145,
    "Салтыков-Щедрин Михаил",
    "John Doe",
])
def test_validate_full_name_valid(name: str):
    """Проверки корректных данных: список ошибок должен быть пустым"""
    errors = validate_full_name(name)
    assert not errors

@pytest.mark.parametrize("name", [
    "",
    "Иванов",
    "А" * 151,
    "Иван123",
    "Иван@Иванов",
])
def test_validate_full_name_invalid(name: str):
    """Некорректное ФИО"""
    errors = validate_full_name(name)
    assert errors

@pytest.mark.parametrize("position", [
    "Оператор",
    "А" * 50,
])
def test_validate_position_valid(position: str):
    """Корректная должность"""
    errors = validate_position(position)
    assert not errors

@pytest.mark.parametrize("position", [
    "",
    "А" * 51,
])
def test_validate_position_invalid(position: str):
    """Некорректная должность"""
    errors = validate_position(position)
    assert errors

@pytest.mark.parametrize("username", [
    "usr",
    "a" * 30,
    "user_name",
    "user123",
])
def test_validate_username_valid(username: str):
    """Корректный логин"""
    errors = validate_username(username)
    assert not errors

@pytest.mark.parametrize("username", [
    "ab",
    "a" * 31,
    "пользователь",
    "user name",
])
def test_validate_username_invalid(username: str):
    """Некорректный логин"""
    errors = validate_username(username)
    assert errors

@pytest.mark.parametrize("password", [
    "pass",
    "a" * 64,
])
def test_validate_password_valid(password: str):
    """Корректный пароль"""
    errors = validate_password(password)
    assert not errors

@pytest.mark.parametrize("password", [
    "",
    "123",
    "a" * 65,
])
def test_validate_password_invalid(password: str):
    """Некорректный пароль"""
    errors = validate_password(password)
    assert errors


# ==========================================
# ШАГ 2: Валидаторы с подставными репозиториями
# ==========================================

def test_validate_shift_employee_not_found(test_shift):
    """Сотрудник не найден (employees.get возвращает None)"""
    emp_repo = MagicMock()
    emp_repo.get.return_value = None
    shift_repo = MagicMock()

    errors = validate_shift(test_shift, emp_repo, shift_repo)
    assert errors

def test_validate_shift_overlapping(test_shift):
    """Пересечение (find_overlapping возвращает смену)"""
    emp_repo = MagicMock()
    emp_repo.get.return_value = MagicMock()
    shift_repo = MagicMock()
    shift_repo.find_overlapping.return_value = [test_shift]

    errors = validate_shift(test_shift, emp_repo, shift_repo)
    assert errors

def test_validate_shift_too_long(test_shift):
    """Смена больше 24 часов"""
    emp_repo = MagicMock()
    emp_repo.get.return_value = MagicMock()
    shift_repo = MagicMock()
    shift_repo.find_overlapping.return_value = []

    test_shift.end_at = test_shift.start_at + timedelta(hours=25)

    errors = validate_shift(test_shift, emp_repo, shift_repo)
    assert errors

def test_validate_shift_valid(test_shift):
    """Всё корректно, пустой список ошибок"""
    emp_repo = MagicMock()
    emp_repo.get.return_value = MagicMock()
    shift_repo = MagicMock()
    shift_repo.find_overlapping.return_value = []

    errors = validate_shift(test_shift, emp_repo, shift_repo)
    assert not errors

def test_validate_user_login_taken():
    """Логин занят (users.get_by_username возвращает пользователя)"""
    users_repo = MagicMock()
    users_repo.get_by_username.return_value = MagicMock()
    emp_repo = MagicMock()

    errors = validate_user("test_user", "pass123", uuid.uuid4(), users_repo, emp_repo)
    assert errors


def test_validate_user_already_has_account():
    """У сотрудника уже есть учётная запись"""
    users_repo = MagicMock()
    users_repo.get_by_username.return_value = None
    users_repo.get_by_employee_id.return_value = MagicMock()
    emp_repo = MagicMock()

    errors = validate_user("test_user", "pass123", uuid.uuid4(), users_repo, emp_repo)
    assert errors


def test_validate_user_employee_not_found():
    """Сотрудник не найден (employees.get возвращает None)"""
    users_repo = MagicMock()
    users_repo.get_by_username.return_value = None
    users_repo.get_by_employee_id.return_value = None
    emp_repo = MagicMock()
    emp_repo.get.return_value = None

    errors = validate_user("test_user", "pass123", uuid.uuid4(), users_repo, emp_repo)
    assert errors


def test_validate_user_valid():
    """Всё корректно (свободный логин, нет аккаунта, сотрудник существует)"""
    users_repo = MagicMock()
    users_repo.get_by_username.return_value = None
    users_repo.get_by_employee_id.return_value = None
    emp_repo = MagicMock()
    emp_repo.get.return_value = MagicMock()

    errors = validate_user("test_user", "pass123", uuid.uuid4(), users_repo, emp_repo)
    assert not errors