"""Главный модуль веб-интерфейса PAWS."""

import logging
import os
import shutil
import tempfile
import urllib.parse
from datetime import date, time
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask
from starlette.middleware.sessions import SessionMiddleware

from src.api.auth import router as auth_router
from src.api.employees import router as employees_router
from src.api.reports import router as reports_router
from src.api.shifts import router as shifts_router
from src.container import auth_manager, paws_core
from src.report import Report

logger = logging.getLogger(__name__)

app = FastAPI(title="PAWS Web")

app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(shifts_router)
app.include_router(reports_router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Глобальный перехватчик ValueError из сервисного слоя."""
    error_msg = str(exc).lower()

    if any(k in error_msg for k in ["пересекается", "совпадает", "уже существует"]):
        status_code = status.HTTP_409_CONFLICT
    elif "не найден" in error_msg:
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    safe_msg = urllib.parse.quote(str(exc))
    referer = request.headers.get("referer")
    base_url = str(request.base_url)

    if not referer or not referer.startswith(base_url):
        referer = "/"
    if "?" in referer:
        referer = referer.split("?")[0]

    return RedirectResponse(
        url=f"{referer}?error={safe_msg}", status_code=status.HTTP_302_FOUND
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Глобальный перехватчик ошибок валидации Pydantic (422).
    Форматирует стандартный список ошибок FastAPI в единую понятную строку.
    """
    error_messages = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"])
        error_messages.append(f"[{loc}]: {err['msg']}")

    detail_str = "; ".join(error_messages)

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": detail_str},
        )

    safe_msg = urllib.parse.quote(detail_str)
    referer = request.headers.get("referer")
    base_url = str(request.base_url)

    if not referer or not referer.startswith(base_url):
        referer = "/"
    if "?" in referer:
        referer = referer.split("?")[0]

    return RedirectResponse(
        url=f"{referer}?error={safe_msg}", status_code=status.HTTP_302_FOUND
    )


secret = os.environ["SESSION_SECRET"]
app.add_middleware(SessionMiddleware, secret_key=secret)

app.mount("/static", StaticFiles(directory="web"), name="static")
templates = Jinja2Templates(directory="web")


def get_current_user(request: Request) -> str | None:
    """Возвращает текущего пользователя из сессии."""
    return request.session.get("user")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Отображает страницу входа."""
    return templates.TemplateResponse(
        request=request, name="login.html", context={"title": "Вход в PAWS"}
    )


@app.post("/login")
async def login_post(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    """Обрабатывает данные формы авторизации."""
    try:
        user = auth_manager.login(username, password)
        request.session["user"] = getattr(user, "username", str(user))
        request.session["role"] = user.role.value
        request.session["user_id"] = str(user.employee_id)
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"title": "Вход в PAWS", "error": str(e)},
        )


@app.get("/logout")
async def logout(request: Request):
    """Очищает сессию пользователя и выходит из аккаунта."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    employee_id: str | None = None,
    error: str | None = None,
    current_user: str = Depends(get_current_user),
):
    """Отображает дашборд управления сменами."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    emp_uuid = None
    if employee_id and employee_id.strip():
        try:
            emp_uuid = UUID(employee_id.strip())
        except ValueError:
            pass

    shifts = paws_core.list_shifts(employee_id=emp_uuid)
    employees = paws_core.list_employees()

    context = {
        "title": "PAWS - Управление сменами",
        "username": current_user,
        "shifts": shifts,
        "employees": employees,
        "selected_employee": str(employee_id) if employee_id else "",
        "error": error,
    }
    return templates.TemplateResponse(
        request=request, name="index.html", context=context
    )


@app.post("/shifts/add")
async def add_shift(
    request: Request,
    employee_id: str = Form(...),
    shift_date: str = Form(...),
    time_start: str = Form(...),
    time_end: str = Form(...),
    description: str = Form(""),
    current_user: str = Depends(get_current_user),
):
    """Добавляет новую смену через веб-интерфейс."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    if request.session.get("role") not in ["admin", "manager"]:
        error_msg = urllib.parse.quote("Недостаточно прав для добавления смены.")
        return RedirectResponse(
            url=f"/?error={error_msg}", status_code=status.HTTP_302_FOUND
        )

    try:
        emp_uuid = UUID(employee_id.strip())
        s_date = date.fromisoformat(shift_date)
        s_start = time.fromisoformat(time_start)
        s_end = time.fromisoformat(time_end)

        paws_core.add_shift(
            employee_id=emp_uuid,
            shift_date=s_date,
            start=s_start,
            end=s_end,
            description=description,
        )
    except ValueError as e:
        error_msg = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"/?error={error_msg}", status_code=status.HTTP_302_FOUND
        )

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/employees", response_class=HTMLResponse)
async def employees_page(
    request: Request,
    error: str | None = None,
    current_user: str = Depends(get_current_user),
):
    """Отображает список всех сотрудников."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    employees = paws_core.list_employees()
    context = {
        "title": "PAWS - Сотрудники",
        "username": current_user,
        "employees": employees,
        "error": error,
    }
    return templates.TemplateResponse(
        request=request, name="employees.html", context=context
    )


@app.post("/employees/add")
async def add_employee(
    request: Request,
    full_name: str = Form(...),
    position: str = Form(""),
    current_user: str = Depends(get_current_user),
):
    """Создает нового сотрудника через веб-интерфейс."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    if request.session.get("role") not in ["admin", "manager"]:
        error_msg = urllib.parse.quote("Недостаточно прав.")
        return RedirectResponse(
            url=f"/employees?error={error_msg}",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        paws_core.add_employee(full_name=full_name, position=position)
    except ValueError as e:
        error_msg = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"/employees?error={error_msg}",
            status_code=status.HTTP_302_FOUND,
        )

    return RedirectResponse(url="/employees", status_code=status.HTTP_302_FOUND)


def export_response(
    report: Report, fmt: str, date_from: date, date_to: date
) -> FileResponse:
    """Сохраняет отчёт во временный файл и отдаёт его на скачивание."""
    download_name = f"report_{date_from}_{date_to}.{fmt}"
    tmp_dir = tempfile.mkdtemp(prefix="paws_")
    path = os.path.join(tmp_dir, download_name)
    try:
        paws_core.export_report(report, fmt=fmt, filename=path)
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    return FileResponse(
        path,
        filename=download_name,
        media_type="application/octet-stream",
        background=BackgroundTask(shutil.rmtree, tmp_dir, True),
    )


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    error: str | None = None,
    current_user: str = Depends(get_current_user),
):
    """Отображает страницу управления отчетами."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    employees = paws_core.list_employees()
    context = {
        "title": "PAWS - Отчеты",
        "username": current_user,
        "employees": employees,
        "selected_employee": "",
        "error": error,
    }
    return templates.TemplateResponse(
        request=request, name="reports.html", context=context
    )


@app.post("/reports/generate")
async def generate_report_ui(
    request: Request,
    date_from: str = Form(...),
    date_to: str = Form(...),
    employee_id: str = Form(""),
    export_format: str = Form(""),
    current_user: str = Depends(get_current_user),
):
    """Генерирует отчет через веб-интерфейс."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    user_role = request.session.get("role", "employee")

    if user_role not in ["admin", "manager"]:
        session_uid = request.session.get("user_id")
        if not session_uid:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        target_uuid = UUID(session_uid)
    else:
        target_uuid = (
            UUID(employee_id.strip()) if employee_id and employee_id.strip() else None
        )

    employees = paws_core.list_employees()

    try:
        d_from = date.fromisoformat(date_from)
        d_to = date.fromisoformat(date_to)

        report = paws_core.generate_report(
            date_from=d_from, date_to=d_to, employee_id=target_uuid
        )

        if export_format:
            return export_response(report, export_format, d_from, d_to)

        context = {
            "title": "PAWS - Результат отчета",
            "username": current_user,
            "employees": employees,
            "report": report,
            "selected_employee": str(employee_id) if employee_id else "",
            "date_from": date_from,
            "date_to": date_to,
        }
        return templates.TemplateResponse(
            request=request, name="reports.html", context=context
        )

    except ValueError as e:
        error_msg = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"/reports?error={error_msg}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception:
        logger.exception("Ошибка при формировании отчёта")
        error_msg = urllib.parse.quote("Системная ошибка при генерации отчета.")
        return RedirectResponse(
            url=f"/reports?error={error_msg}",
            status_code=status.HTTP_302_FOUND,
        )


def main() -> None:
    """Точка входа для запуска веб-сервера через uv run paws."""
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
