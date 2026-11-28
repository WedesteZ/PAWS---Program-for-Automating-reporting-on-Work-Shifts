"""Тесты HTML-маршрутов веб-интерфейса и выгрузки отчётов (src/main.py)."""

from datetime import date, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.models import Employee, Report, Shift


def _web_login(
    api_client: TestClient,
    mock_auth: MagicMock,
    role: str = "admin",
    employee_id: UUID | None = None,
) -> UUID:
    """Выполняет вход через HTML-форму /login и возвращает ID сотрудника."""
    emp_id = employee_id or uuid4()
    mock_auth.login.return_value = SimpleNamespace(
        username=f"web_{role}",
        role=SimpleNamespace(value=role),
        employee_id=emp_id,
    )
    response = api_client.post(
        "/login",
        data={"username": f"web_{role}", "password": "secret"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    return emp_id


def test_login_page_and_failed_submit(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет рендер /login и отображение ошибки при неверном пароле."""
    _, mock_auth = api_mocks

    get_resp = api_client.get("/login")
    assert get_resp.status_code == 200
    assert "text/html" in get_resp.headers["content-type"]

    mock_auth.login.side_effect = ValueError("Неверный пароль")
    post_resp = api_client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=False,
    )
    assert post_resp.status_code == 200
    assert "Неверный пароль" in post_resp.text


def test_validation_error_on_web_route_redirects(api_client: TestClient) -> None:
    """Проверяет редирект с ?error= при ошибке валидации формы."""
    response = api_client.post("/login", data={}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"].startswith("/?error=")


def test_logout_clears_session_and_redirects(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
) -> None:
    """Проверяет очистку сессии и редирект на /login после выхода."""
    _, mock_auth = api_mocks
    _web_login(api_client, mock_auth, role="admin")

    logout_resp = api_client.get("/logout", follow_redirects=False)
    assert logout_resp.status_code == 302
    assert logout_resp.headers["location"] == "/login"

    dashboard_resp = api_client.get("/", follow_redirects=False)
    assert dashboard_resp.status_code == 302
    assert dashboard_resp.headers["location"] == "/login"


def test_dashboard_redirects_anonymous_and_renders_authenticated(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
    test_shift: Shift,
) -> None:
    """Проверяет защиту / и корректный рендер дашборда с фильтром."""
    mock_core, mock_auth = api_mocks

    anon_resp = api_client.get("/", follow_redirects=False)
    assert anon_resp.status_code == 302
    assert anon_resp.headers["location"] == "/login"

    mock_core.list_shifts.return_value = [test_shift]
    mock_core.list_employees.return_value = [test_employee]
    _web_login(api_client, mock_auth, role="manager", employee_id=test_employee.id)

    bad_uuid_resp = api_client.get("/?employee_id=not-a-uuid")
    assert bad_uuid_resp.status_code == 200
    mock_core.list_shifts.assert_called_with(employee_id=None)

    valid_uuid_resp = api_client.get(f"/?employee_id={test_employee.id}")
    assert valid_uuid_resp.status_code == 200
    mock_core.list_shifts.assert_called_with(employee_id=test_employee.id)


def test_add_shift_web_rbac_and_success(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
) -> None:
    """Проверяет ограничение прав и добавление смены через веб-форму."""
    mock_core, mock_auth = api_mocks
    form_data = {
        "employee_id": str(test_employee.id),
        "shift_date": "2026-11-11",
        "time_start": "09:00",
        "time_end": "18:00",
        "description": "Веб-смена",
    }

    _web_login(api_client, mock_auth, role="employee")
    forbidden_resp = api_client.post(
        "/shifts/add", data=form_data, follow_redirects=False
    )
    assert forbidden_resp.status_code == 302
    assert forbidden_resp.headers["location"].startswith("/?error=")
    mock_core.add_shift.assert_not_called()

    _web_login(api_client, mock_auth, role="manager")
    ok_resp = api_client.post("/shifts/add", data=form_data, follow_redirects=False)
    assert ok_resp.status_code == 302
    assert ok_resp.headers["location"] == "/"
    mock_core.add_shift.assert_called_once_with(
        employee_id=test_employee.id,
        shift_date=date(2026, 11, 11),
        start=time(9, 0),
        end=time(18, 0),
        description="Веб-смена",
    )


def test_employees_page_and_add_employee_web(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
) -> None:
    """Проверяет страницу сотрудников, RBAC и обработку ошибок формы."""
    mock_core, mock_auth = api_mocks
    mock_core.list_employees.return_value = [test_employee]

    _web_login(api_client, mock_auth, role="employee")
    page_resp = api_client.get("/employees")
    assert page_resp.status_code == 200

    forbidden_resp = api_client.post(
        "/employees/add",
        data={"full_name": "Петров Пётр", "position": "Инженер"},
        follow_redirects=False,
    )
    assert forbidden_resp.status_code == 302
    assert forbidden_resp.headers["location"].startswith("/employees?error=")

    _web_login(api_client, mock_auth, role="admin")
    ok_resp = api_client.post(
        "/employees/add",
        data={"full_name": "Петров Пётр", "position": "Инженер"},
        follow_redirects=False,
    )
    assert ok_resp.status_code == 302
    assert ok_resp.headers["location"] == "/employees"
    mock_core.add_employee.assert_called_once_with(
        full_name="Петров Пётр",
        position="Инженер",
    )

    mock_core.add_employee.side_effect = ValueError("Дубликат")
    err_resp = api_client.post(
        "/employees/add",
        data={"full_name": "Петров Пётр", "position": "Инженер"},
        follow_redirects=False,
    )
    assert err_resp.status_code == 302
    assert err_resp.headers["location"].startswith("/employees?error=")


def test_reports_page_render_export_and_os_error(
    api_client: TestClient,
    api_mocks: tuple[MagicMock, MagicMock],
    test_employee: Employee,
    test_report: Report,
) -> None:
    """Проверяет HTML-отчёт, скачивание файла и перехват системной ошибки."""
    mock_core, mock_auth = api_mocks
    mock_core.list_employees.return_value = [test_employee]
    mock_core.generate_report.return_value = test_report

    own_id = _web_login(api_client, mock_auth, role="employee")

    page_resp = api_client.get("/reports")
    assert page_resp.status_code == 200

    html_resp = api_client.post(
        "/reports/generate",
        data={
            "date_from": "2026-11-01",
            "date_to": "2026-11-30",
            "employee_id": str(uuid4()),
            "export_format": "",
        },
    )
    assert html_resp.status_code == 200
    mock_core.generate_report.assert_called_with(
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 30),
        employee_id=own_id,
    )

    def _write_dummy_export(report: Report, fmt: str, filename: str) -> None:
        Path(filename).write_bytes(b"fake-xlsx-report")

    mock_core.export_report.side_effect = _write_dummy_export
    file_resp = api_client.post(
        "/reports/generate",
        data={
            "date_from": "2026-11-01",
            "date_to": "2026-11-30",
            "export_format": "xlsx",
        },
        follow_redirects=False,
    )
    assert file_resp.status_code == 200
    assert file_resp.content == b"fake-xlsx-report"
    assert (
        "report_2026-11-01_2026-11-30.xlsx" in file_resp.headers["content-disposition"]
    )

    mock_core.export_report.side_effect = OSError("Диск переполнен")
    os_err_resp = api_client.post(
        "/reports/generate",
        data={
            "date_from": "2026-11-01",
            "date_to": "2026-11-30",
            "export_format": "xlsx",
        },
        follow_redirects=False,
    )
    assert os_err_resp.status_code == 302
    assert os_err_resp.headers["location"].startswith("/reports?error=")
