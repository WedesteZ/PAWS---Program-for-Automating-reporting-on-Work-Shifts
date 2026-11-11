import pytest

from src.security import hash_password, verify_password


def test_hash_password_salts(monkeypatch: pytest.MonkeyPatch):
    """Хэши одного и того же пароля должны различаться из-за случайной соли."""
    monkeypatch.setattr("src.security.ITERATIONS", 1000)

    password = "my_secure_password"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2


def test_verify_password(monkeypatch: pytest.MonkeyPatch):
    """Проверка верификации: верный, неверный и пустой пароль."""
    monkeypatch.setattr("src.security.ITERATIONS", 1000)

    password = "secret_password"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
    assert verify_password("", hashed) is False
