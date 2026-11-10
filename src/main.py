"""Главный модуль веб-интерфейса PAWS."""
import os
import urllib.parse
from datetime import date, time
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.app import PawsApp
from src.auth import AuthManager
from src.demo import seed_demo_data

# Инициализация ядра
paws_core = PawsApp()
auth_manager = AuthManager()  # Убрали paws_core.storage
seed_demo_data(paws_core, auth_manager)

app = FastAPI(title="PAWS Web")

# Подключение сессий с секретом из .env
secret = os.getenv("SESSION_SECRET", "default-insecure-secret")
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
    return templates.TemplateResponse(request=request, name="index.html", context=context)


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
    """Добавляет новую смену в систему."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

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
async def employees_page(request: Request, current_user: str = Depends(get_current_user)):
    """Отображает список всех сотрудников."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    employees = paws_core.list_employees()
    context = {
        "title": "PAWS - Сотрудники",
        "username": current_user,
        "employees": employees,
    }
    return templates.TemplateResponse(
        request=request, name="employees.html", context=context
    )


@app.post("/employees/add")
async def add_employee(
    full_name: str = Form(...),
    position: str = Form(""),
    current_user: str = Depends(get_current_user),
):
    """Создает нового сотрудника."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    paws_core.add_employee(full_name=full_name, position=position)
    return RedirectResponse(url="/employees", status_code=status.HTTP_302_FOUND)


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
        "error": error,
    }
    return templates.TemplateResponse(request=request, name="reports.html", context=context)


@app.post("/reports/generate")
async def generate_report(
    request: Request,
    date_from: str = Form(...),
    date_to: str = Form(...),
    employee_id: str = Form(""),
    export_format: str = Form(""),
    current_user: str = Depends(get_current_user),
):
    """Генерирует и при необходимости экспортирует отчет за период."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    employees = paws_core.list_employees()

    try:
        emp_uuid = None
        if employee_id and employee_id.strip():
            emp_uuid = UUID(employee_id.strip())

        d_from = date.fromisoformat(date_from)
        d_to = date.fromisoformat(date_to)

        report = paws_core.generate_report(
            date_from=d_from, date_to=d_to, employee_id=emp_uuid
        )

        if export_format:
            filename = f"report_{date_from}_{date_to}.{export_format}"
            paws_core.export_report(report, fmt=export_format, filename=filename)
            return FileResponse(
                filename, filename=filename, media_type="application/octet-stream"
            )

        context = {
            "title": "PAWS - Результат отчета",
            "username": current_user,
            "employees": employees,
            "report": report,
            "date_from": date_from,
            "date_to": date_to,
        }
        return templates.TemplateResponse(
            request=request, name="reports.html", context=context
        )

    except Exception as e:
        error_msg = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"/reports?error={error_msg}", status_code=status.HTTP_302_FOUND
        )


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)