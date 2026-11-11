import pytest

from src.validation import (
    validate_full_name,
    validate_password,
    validate_position,
    validate_username,
)

"""Проверки корректных данных: список ошибок должен быть пустым"""
@pytest.mark.parametrize("name", [
    "Иванов Иван",
    "Иван " + "А" * 145,
    "Салтыков-Щедрин Михаил",
    "John Doe",
])
def test_validate_full_name_valid(name: str):
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
    errors = validate_full_name(name)
    assert errors

@pytest.mark.parametrize("position", [
    "Оператор",
    "А" * 50,
])
def test_validate_position_valid(position: str):
    errors = validate_position(position)
    assert not errors

@pytest.mark.parametrize("position", [
    "",
    "А" * 51,
])
def test_validate_position_invalid(position: str):
    errors = validate_position(position)
    assert errors

@pytest.mark.parametrize("username", [
    "usr",
    "a" * 30,
    "user_name",
    "user123",
])
def test_validate_username_valid(username: str):
    errors = validate_username(username)
    assert not errors

@pytest.mark.parametrize("username", [
    "ab",
    "a" * 31,
    "пользователь",
    "user name",
])
def test_validate_username_invalid(username: str):
    errors = validate_username(username)
    assert errors

@pytest.mark.parametrize("password", [
    "pass",
    "a" * 64,
])
def test_validate_password_valid(password: str):
    errors = validate_password(password)
    assert not errors

@pytest.mark.parametrize("password", [
    "",
    "123",
    "a" * 65,
])
def test_validate_password_invalid(password: str):
    errors = validate_password(password)
    assert errors