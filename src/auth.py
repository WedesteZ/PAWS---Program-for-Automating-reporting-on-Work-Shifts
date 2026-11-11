import uuid

from sqlalchemy.orm import Session, sessionmaker

from src import SessionLocal
from src import Role, User
from src import EmployeeRepository, UserRepository
from src import hash_password, verify_password
from src import validate_user


class AuthManager:
    """Управление учётными записями пользователей системы."""

    def __init__(
        self, session_factory: sessionmaker[Session] = SessionLocal
    ) -> None:
        self.session_factory = session_factory

    def add_user(
        self, username: str, password: str, employee_id: uuid.UUID, role: Role
    ) -> User:
        """Создаёт нового пользователя после проверки данных.

        Raises:
            ValueError: если данные не прошли валидацию.
        """
        with self.session_factory.begin() as session:
            users = UserRepository(session)
            employees = EmployeeRepository(session)
            errors = validate_user(username, password, employee_id, users, employees)
            if errors:
                raise ValueError("; ".join(errors))
            user = User(
                username=username,
                password_hash=hash_password(password),
                employee_id=employee_id,
                role=role,
            )
            return users.add(user)

    def list_users(self) -> list[User]:
        """Возвращает список всех зарегистрированных пользователей."""
        with self.session_factory() as session:
            return UserRepository(session).list_all()

    def login(self, username: str, password: str) -> User:
        """Проверяет учётные данные и возвращает пользователя при успехе.

        Raises:
            ValueError: если логин или пароль неверны.
        """
        with self.session_factory() as session:
            user = UserRepository(session).get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Неверное имя пользователя или пароль")
        return user
