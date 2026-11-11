"""API роутер для аутентификации."""
from fastapi import APIRouter

from src.container import auth_manager
from src.dtos.requests import LoginRequest
from src.dtos.responses import UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=UserOut,
    summary="Авторизация",
    description="Проверяет логин/пароль и возвращает профиль пользователя.",
    responses={404: {"description": "Пользователь не найден или неверный пароль"}},
)
def login(credentials: LoginRequest) -> UserOut:
    """Выполняет вход и возвращает данные пользователя."""
    user = auth_manager.login(credentials.username, credentials.password)
    return UserOut(username=user.username, role=user.role.value)