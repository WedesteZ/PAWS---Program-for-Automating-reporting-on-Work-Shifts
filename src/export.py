"""Модуль для экспорта отчетов в различные форматы."""
import csv
import json
from pathlib import Path
from abc import ABC, abstractmethod

import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.models import Report


class Exporter(ABC):
    """Базовый абстрактный класс экспортёра."""

    @abstractmethod
    def export(self, report: Report, filename: str) -> str:
        """Экспортирует отчет в файл."""
        pass


class CsvExporter(Exporter):
    """Экспорт отчета в формат CSV."""

    def export(self, report: Report, filename: str) -> str:
        with open(filename, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([report.text])
            writer.writerow(["Дата", "Сотрудник", "Начало", "Конец", "Часы", "Описание"])
            for row in report.rows:
                writer.writerow([
                    row.shift_date, str(row.employee), row.time_start,
                    row.time_end, row.hours, row.description
                ])
            writer.writerow([])
            writer.writerow(["Итого часов:", report.total_hours])
        return filename


class JsonExporter(Exporter):
    """Экспорт отчета в формат JSON."""

    def export(self, report: Report, filename: str) -> str:
        data = {
            "title": report.text,
            "total_hours": report.total_hours,
            "rows": [
                {
                    "date": str(r.shift_date),
                    "employee": str(r.employee),
                    "time_start": str(r.time_start),
                    "time_end": str(r.time_end),
                    "hours": r.hours,
                    "description": r.description
                } for r in report.rows
            ]
        }
        with open(filename, mode="w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return filename


class XlsxExporter(Exporter):
    """Экспорт отчета в формат Excel (XLSX)."""

    def export(self, report: Report, filename: str) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Отчет PAWS"

        ws.append([report.text])
        ws.append([])

        ws.append(["Дата", "Сотрудник", "Начало", "Конец", "Часы", "Описание"])
        for row in report.rows:
            ws.append([
                str(row.shift_date),
                str(row.employee),
                str(row.time_start),
                str(row.time_end),
                row.hours,
                row.description
            ])

        ws.append([])
        ws.append(["Итого часов:", report.total_hours])

        wb.save(filename)
        return filename


class PdfExporter(Exporter):
    """Экспорт отчета в формат PDF с поддержкой кириллицы."""

    def export(self, report: Report, filename: str) -> str:
        font_path = Path(__file__).resolve().parent.parent / 'DejaVuSans.ttf'
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', str(font_path)))
            font_name = 'DejaVu'
        except Exception:
            font_name = 'Helvetica'

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        c.setFont(font_name, 14)
        title_text = report.text.split('\n')[0] if report.text else "Отчет"
        c.drawString(50, height - 50, title_text)

        c.setFont(font_name, 10)
        y = height - 80

        c.drawString(50, y, "Дата")
        c.drawString(130, y, "Сотрудник")
        c.drawString(270, y, "Время")
        c.drawString(350, y, "Часы")
        c.drawString(400, y, "Описание")

        y -= 20
        c.line(50, y + 15, 550, y + 15)

        for row in report.rows:
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont(font_name, 10)

            c.drawString(50, y, str(row.shift_date))
            c.drawString(130, y, str(row.employee)[:20])
            c.drawString(270, y, f"{row.time_start}-{row.time_end}")
            c.drawString(350, y, str(row.hours))
            c.drawString(400, y, str(row.description)[:30])
            y -= 20

        y -= 10
        c.line(50, y + 15, 550, y + 15)
        c.drawString(50, y, f"Итого часов: {report.total_hours}")

        c.save()
        return filename


# Словарь всех доступных экспортёров (Пункт 1)
EXPORTERS = {
    "csv": CsvExporter,
    "json": JsonExporter,
    "xlsx": XlsxExporter,
    "pdf": PdfExporter
}


def get_exporter(fmt: str) -> Exporter:
    """
    Фабрика для получения нужного экспортёра по формату.

    Args:
        fmt (str): Название формата (например, 'pdf', 'csv').

    Returns:
        Exporter: Экземпляр класса экспортёра.

    Raises:
        ValueError: Если формат не поддерживается.
    """
    fmt = fmt.lower()
    exporter_class = EXPORTERS.get(fmt)
    if not exporter_class:
        raise ValueError(f"Неизвестный формат отчёта: {fmt}")
    return exporter_class()