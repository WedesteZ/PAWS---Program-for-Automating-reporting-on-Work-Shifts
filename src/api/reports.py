from fastapi import APIRouter, Depends, Request
from src.api.dependencies import RequireManagerOrAdmin
from src.dtos.requests import ReportRequest
from src.dtos.responses import ReportOut
from src.main import paws_core

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.post(
    "/generate",
    response_model=ReportOut,
    summary="Сгенерировать отчет",
    description="Формирует агрегированный отчет по отработанным часам.",
    responses={403: {"description": "Недостаточно прав"}},
)
def generate_report(request: Request, report_in: ReportRequest, _: RequireManagerOrAdmin):
    # Ограничение B9: employee не имеет доступа к API отчетов
    report = paws_core.generate_report(
        date_from=report_in.date_from,
        date_to=report_in.date_to,
        employee_id=report_in.employee_id
    )
    return report