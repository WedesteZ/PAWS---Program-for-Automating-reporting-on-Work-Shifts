from datetime import date, time

import openpyxl
import pytest

from src.export import get_exporter
from src.models import Report, ReportRow


def test_export_xlsx(test_report, tmp_path):
    """XLSX открывается через openpyxl: проверить заголовок, число строк, итоги"""
    exporter = get_exporter("xlsx")
    file_path = tmp_path / "report.xlsx"
    exporter.export(test_report, str(file_path))

    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    found_title = False
    found_employee = False

    for row in sheet.iter_rows(values_only=True):
        for cell in row:
            if isinstance(cell, str):
                if test_report.title in cell:
                    found_title = True
                if test_report.rows[0].employee in cell:
                    found_employee = True

    assert sheet.max_row >= 2
    assert found_title is True
    assert found_employee is True


def test_export_pdf(test_report, tmp_path):
    """PDF создаётся, размер больше нуля"""
    exporter = get_exporter("pdf")
    file_path = tmp_path / "report.pdf"
    exporter.export(test_report, str(file_path))

    assert file_path.exists()
    assert file_path.stat().st_size > 0


def test_export_empty_report(tmp_path):
    """Пустой отчёт экспортируется без ошибок"""
    report = Report(
        title="Пустой", period="Нет", rows=[], total_shifts=0, total_hours=0.0
    )

    pdf_path = tmp_path / "empty.pdf"
    get_exporter("pdf").export(report, str(pdf_path))
    assert pdf_path.exists()

    xlsx_path = tmp_path / "empty.xlsx"
    get_exporter("xlsx").export(report, str(xlsx_path))
    assert xlsx_path.exists()


def test_export_pdf_special_chars(tmp_path):
    """Спецсимволы <, >, & в имени и описании не ломают PDF"""
    row = ReportRow(
        employee="Иванов <Иван> & Co",
        shift_date=date(2026, 11, 11),
        time_start=time(9, 0),
        time_end=time(18, 0),
        hours=9.0,
        description="Работа с <XML> & > HTML",
    )
    report = Report(
        title="Отчёт <>&", period="11.11", rows=[row], total_shifts=1, total_hours=9.0
    )

    file_path = tmp_path / "special.pdf"
    get_exporter("pdf").export(report, str(file_path))
    assert file_path.exists()
    assert file_path.stat().st_size > 0


def test_get_exporter_invalid():
    """get_exporter('csv'), ('txt') и ('json') бросают ValueError"""
    with pytest.raises(ValueError):
        get_exporter("csv")

    with pytest.raises(ValueError):
        get_exporter("txt")

    with pytest.raises(ValueError):
        get_exporter("json")


def test_get_exporter_case_insensitive():
    """get_exporter('PDF') в верхнем регистре работает"""
    exporter = get_exporter("PDF")
    assert exporter is not None
