"""API роутер для генерации отчетов."""
from fastapi import APIRouter, Request

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
    """Сборка отчета с жесткой привязкой ID для рядовых сотрудников."""
    user_role = request.session.get("role", "employee")

    if user_role not in ["admin", "manager"]:
        target_employee_id = request.session.get("user_id")
    else:
        target_employee_id = report_in.employee_id

    return paws_core.generate_report(
        date_from=report_in.date_from,
        date_to=report_in.date_to,
        employee_id=target_employee_id,
    )