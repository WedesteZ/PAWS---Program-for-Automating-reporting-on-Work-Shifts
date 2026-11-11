from typing import Annotated

from fastapi import Depends, HTTPException, Request, status


def get_current_user(request: Request) -> str:
    """Проверяет, авторизован ли пользователь в сессии."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация",
        )
    return user


def RoleChecker(allowed_roles: list[str]):
    """Генератор зависимостей для проверки ролей (RBAC)."""

    def role_dependency(request: Request, user: str = Depends(get_current_user)) -> str:
        role = request.session.get("role", "employee")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции",
            )
        return role

    return role_dependency


# Готовые зависимости для инъекций
CurrentUser = Annotated[str, Depends(get_current_user)]
RequireManagerOrAdmin = Annotated[str, Depends(RoleChecker(["admin", "manager"]))]
