"""API роутер для генерации отчетов."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from src.api.dependencies import CurrentUser
from src.container import paws_core
from src.dtos.requests import ReportRequest
from src.dtos.responses import ReportOut

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post(
    "/generate",
    response_model=ReportOut,
    summary="Сгенерировать отчет",
    description="Формирует агрегированный отчет по отработанным часам.",
    responses={401: {"description": "Необходима авторизация"}},
)
def generate_report(
    request: Request, report_in: ReportRequest, _: CurrentUser
) -> ReportOut:
    """Сборка отчета с привязкой ID для рядовых сотрудников."""
    user_role = request.session.get("role", "employee")

    if user_role not in ["admin", "manager"]:
        session_user_id = request.session.get("user_id")
        if not session_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия устарела. Пожалуйста, выполните вход заново.",
            )
        target_employee_id = UUID(session_user_id)
    else:
        target_employee_id = report_in.employee_id

    return paws_core.generate_report(
        date_from=report_in.date_from,
        date_to=report_in.date_to,
        employee_id=target_employee_id,
    )