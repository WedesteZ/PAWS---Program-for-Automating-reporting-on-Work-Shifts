import json
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import csv
from abc import ABC, abstractmethod

from src.models import Report


class Exporter(ABC):
    """Абстрактный класс экспорта отчёта в файл."""

    @abstractmethod
    def export(self, report: Report, filename: str) -> str:
        """Сохраняет отчёт в файл. Возвращает имя файла."""


class TxtExporter(Exporter):
    """Экспорт отчёта в текстовый файл."""

    def export(self, report: Report, filename: str) -> str:
        """Сохраняет текстовое представление отчёта. Возвращает имя файла."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report.text)
        return filename


class CsvExporter(Exporter):
    """Экспорт отчёта в CSV (разделитель ';', кодировка UTF-8 с BOM для Excel)."""

    def get_exporter(fmt: str) -> Exporter:
        """
        Фабрика для получения нужного экспортёра по названию формата.

        Raises:
            ValueError: если передан неизвестный формат.
        """
        fmt = fmt.lower()
        if fmt == "csv":
            return CSVExporter()
        elif fmt == "txt":  # Если этот формат был в вашей старой версии
            return TXTExporter()
        elif fmt == "json":
            return JSONExporter()
        elif fmt in ("xlsx", "excel"):
            return XLSXExporter()
        elif fmt == "pdf":
            return PDFExporter()
        else:
            raise ValueError(f"Неизвестный формат отчёта: {fmt}")

class JSONExporter(Exporter):
    """Экспорт отчета в формат JSON."""

    def export(self, report: Report, filename: str) -> str:
        data = {
            "title": report.title,
            "total_hours": report.total_hours,
            "rows": [
                {
                    "date": str(r.date),
                    "employee_name": r.employee_name,
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


class XLSXExporter(Exporter):
    """Экспорт отчета в формат Excel (XLSX)."""

    def export(self, report: Report, filename: str) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Отчет PAWS"

        ws.append([report.title])
        ws.append([])

        headers = ["Дата", "Сотрудник", "Начало", "Конец", "Часы", "Описание"]
        ws.append(headers)

        for row in report.rows:
            ws.append([
                str(row.date),
                row.employee_name,
                str(row.time_start),
                str(row.time_end),
                row.hours,
                row.description
            ])

        ws.append([])
        ws.append(["Итого часов:", report.total_hours])

        wb.save(filename)
        return filename


class PDFExporter(Exporter):
    """Экспорт отчета в формат PDF с поддержкой кириллицы."""

    def export(self, report: Report, filename: str) -> str:
        # Регистрация TTF-шрифта для поддержки русского языка
        # Файл DejaVuSans.ttf должен лежать в корне проекта или в папке с ресурсами
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
            font_name = 'DejaVu'
        except Exception:
            font_name = 'Helvetica'  # Резервный вариант, если файл шрифта не найден

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        c.setFont(font_name, 14)
        c.drawString(50, height - 50, report.title)

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

            c.drawString(50, y, str(row.date))
            c.drawString(130, y, str(row.employee_name)[:20])
            c.drawString(270, y, f"{row.time_start}-{row.time_end}")
            c.drawString(350, y, str(row.hours))
            c.drawString(400, y, str(row.description)[:30])
            y -= 20

        y -= 10
        c.line(50, y + 15, 550, y + 15)
        c.drawString(50, y, f"Итого часов: {report.total_hours}")

        c.save()
        return filename

EXPORTERS: dict[str, type[Exporter]] = {
    "txt": TxtExporter,
    "csv": CsvExporter,
}


def get_exporter(fmt: str) -> Exporter:
    """Возвращает экспортёр для формата fmt.

    Raises:
        ValueError: если такого формата нет среди EXPORTERS.
    """
    exporter_class = EXPORTERS.get(fmt.strip().lower())
    if exporter_class is None:
        raise ValueError(f"Неизвестный формат отчёта: {fmt}")
    return exporter_class()
