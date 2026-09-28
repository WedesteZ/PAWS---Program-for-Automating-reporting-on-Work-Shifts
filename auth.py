from db import Storage
from models import Role, User
from validation import validate_user


class AuthManager:
    """Управление учётными записями пользователей системы."""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def add_user(self, username: str, password: str,
                 employee_id: str, role: Role) -> User:
        """Создаёт нового пользователя после проверки данных.

        Raises:
            ValueError: если данные не прошли валидацию.
        """
        errors = validate_user(username, password, employee_id, self.storage)
        if errors:
            raise ValueError("; ".join(errors))
        user = User(username=username, password=password,
                    employee_id=employee_id, role=role)
        return self.storage.add_user(user)

    def list_users(self) -> list[User]:
        """Возвращает список всех зарегистрированных пользователей."""
        return list(self.storage.users.values())

    def login(self, username: str, password: str) -> User:
        """Проверяет учётные данные и возвращает пользователя при успехе.

        Raises:
            ValueError: если логин или пароль неверны.
        """
        user = self.storage.users.get(username)
        if user is None or user.password != password:
            raise ValueError("Неверное имя пользователя или пароль")
        return user