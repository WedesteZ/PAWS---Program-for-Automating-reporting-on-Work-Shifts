"""API роутер для генерации отчетов."""

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import CurrentSession
from src.container import paws_core
from src.dtos.requests import ReportRequest
from src.dtos.responses import ReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post(
    "/generate",
    summary="Сгенерировать отчет",
    description="Формирует агрегированный отчет по отработанным часам.",
    responses={
        400: {"description": "Ошибка бизнес-валидации"},
        401: {"description": "Необходима авторизация"},
        422: {"description": "Ошибка формата данных"},
    },
)
def generate_report(
    report_in: ReportRequest, current_user: CurrentSession
) -> ReportResponse:
    """Сборка отчета с привязкой ID для рядовых сотрудников."""
    if current_user.role not in ("admin", "manager"):
        if current_user.employee_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия устарела. Пожалуйста, выполните вход заново.",
            )
        target_employee_id = current_user.employee_id
    else:
        target_employee_id = report_in.employee_id

    report = paws_core.generate_report(
        date_from=report_in.date_from,
        date_to=report_in.date_to,
        employee_id=target_employee_id,
    )
    return ReportResponse.model_validate(report)