"""API роутер для аутентификации."""

from fastapi import APIRouter, HTTPException, Request, status

from src.container import auth_manager
from src.dtos.requests import LoginRequest
from src.dtos.responses import UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    summary="Авторизация",
    description="Выполняет вход, создает сессию и возвращает профиль пользователя.",
    responses={
        401: {"description": "Неверный логин или пароль"},
        422: {"description": "Ошибка формата данных"},
    },
)
def login(credentials: LoginRequest, request: Request) -> UserResponse:
    """Выполняет вход и возвращает данные пользователя."""
    try:
        user = auth_manager.login(credentials.username, credentials.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from None

    request.session["user"] = getattr(user, "username", str(user))
    request.session["role"] = user.role.value
    request.session["user_id"] = str(user.employee_id)

    return UserResponse(username=user.username, role=user.role.value)