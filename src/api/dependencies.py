from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status


@dataclass(frozen=True)
class SessionUser:
    """Данные авторизованного пользователя из текущей сессии."""

    username: str
    role: str
    employee_id: UUID | None


def get_current_user(request: Request) -> str:
    """Проверяет, авторизован ли пользователь в сессии."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация",
        )
    return user


def get_current_session(request: Request) -> SessionUser:
    """Возвращает данные пользователя, роль и ID сотрудника из сессии."""
    username = get_current_user(request)
    role = request.session.get("role", "employee")
    raw_user_id = request.session.get("user_id")
    employee_id = UUID(raw_user_id) if raw_user_id else None
    return SessionUser(username=username, role=role, employee_id=employee_id)


def RoleChecker(allowed_roles: list[str]) -> Callable[[Request], str]:
    """Генератор зависимостей для проверки ролей (RBAC)."""

    def role_dependency(request: Request) -> str:
        """Проверяет наличие необходимой роли у текущего пользователя."""
        get_current_user(request)
        role = request.session.get("role", "employee")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции",
            )
        return role

    return role_dependency


require_manager_or_admin = RoleChecker(["admin", "manager"])
CurrentSession = Annotated[SessionUser, Depends(get_current_session)]