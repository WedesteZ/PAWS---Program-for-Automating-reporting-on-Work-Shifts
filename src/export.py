"""Модуль для экспорта отчётов в различные форматы."""

from abc import ABC, abstractmethod
from datetime import date, time
from pathlib import Path
from xml.sax.saxutils import escape

import openpyxl
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models import Report

FONT_PATH = Path(__file__).resolve().parent.parent / "DejaVuSans.ttf"
HEADERS = ["Дата", "Сотрудник", "Начало", "Конец", "Часы", "Описание"]


def _title(report: Report) -> str:
    """Возвращает заголовок отчёта."""
    return report.title or report.text.split("\n")[0] or "Отчёт"


def _date(value: date) -> str:
    """Форматирует дату как ДД.ММ.ГГГГ."""
    return f"{value:%d.%m.%Y}"


def _time(value: time) -> str:
    """Форматирует время как ЧЧ:ММ."""
    return f"{value:%H:%M}"


def _period_line(report: Report) -> str:
    """Возвращает строку с периодом отчёта (пустую, если период не задан)."""
    return f"Период: {report.period}" if report.period else ""


def _summary(report: Report) -> str:
    """Возвращает итоговую строку: число смен и сумма часов."""
    return f"Всего смен: {report.total_shifts}; всего часов: {report.total_hours}"


class Exporter(ABC):
    """Базовый абстрактный класс экспортёра."""

    @abstractmethod
    def export(self, report: Report, filename: str) -> str:
        """Экспортирует отчёт в файл.

        Args:
            report: Объект отчёта с данными.
            filename: Имя файла для сохранения.

        Returns:
            Путь к сохранённому файлу.
        """


class TxtExporter(Exporter):
    """Экспорт отчёта в простой текстовый формат."""

    def export(self, report: Report, filename: str) -> str:
        """Записывает готовый текст отчёта в файл."""
        with open(filename, mode="w", encoding="utf-8") as f:
            f.write(report.text)
        return filename


class XlsxExporter(Exporter):
    """Экспорт отчёта в формат Excel (XLSX)."""

    WIDTHS = (12, 40, 9, 9, 8, 50)

    def export(self, report: Report, filename: str) -> str:
        """Записывает отчёт в XLSX с заголовками и итогами."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Отчёт PAWS"
        bold = Font(bold=True)

        ws.append([_title(report)])
        ws.append([_period_line(report)])
        ws.append([])
        ws.append(HEADERS)
        header_row = ws.max_row
        for row in report.rows:
            ws.append(
                [
                    _date(row.shift_date),
                    row.employee,
                    _time(row.time_start),
                    _time(row.time_end),
                    row.hours,
                    row.description,
                ]
            )
        ws.append([])
        ws.append(["Всего смен:", report.total_shifts])
        ws.append(["Всего часов:", report.total_hours])

        ws["A1"].font = Font(bold=True, size=14)
        for cell in ws[header_row]:
            cell.font = bold
        for column, width in zip("ABCDEF", self.WIDTHS, strict=True):
            ws.column_dimensions[column].width = width
        ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

        wb.save(filename)
        return filename


class PdfExporter(Exporter):
    """Экспорт отчёта в формат PDF с поддержкой кириллицы."""

    FONT = "DejaVu"

    def export(self, report: Report, filename: str) -> str:
        """Записывает отчёт в PDF: длинный текст переносится, шапка повторяется.

        Raises:
            ValueError: если не найден файл шрифта с кириллицей.
        """
        if not FONT_PATH.exists():
            raise ValueError("Не найден шрифт DejaVuSans.ttf для PDF-отчёта")
        if self.FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(self.FONT, str(FONT_PATH)))

        title_style = ParagraphStyle(
            "title", fontName=self.FONT, fontSize=14, leading=20
        )
        text_style = ParagraphStyle("text", fontName=self.FONT, fontSize=9, leading=11)
        head_style = ParagraphStyle("head", parent=text_style, textColor=colors.white)

        def cell(value: object, style: ParagraphStyle = text_style) -> Paragraph:
            return Paragraph(escape(str(value)), style)

        data = [[cell(h, head_style) for h in HEADERS]]
        for row in report.rows:
            data.append(
                [
                    cell(_date(row.shift_date)),
                    cell(row.employee),
                    cell(_time(row.time_start)),
                    cell(_time(row.time_end)),
                    cell(row.hours),
                    cell(row.description),
                ]
            )

        table = Table(
            data,
            colWidths=[70, 125, 48, 46, 38, 188],
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story = [Paragraph(escape(_title(report)), title_style)]
        if report.period:
            story.append(Paragraph(escape(_period_line(report)), text_style))
        story += [Spacer(1, 10), table, Spacer(1, 10)]
        story.append(Paragraph(escape(_summary(report)), text_style))

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=40,
            bottomMargin=40,
        )
        doc.build(story)
        return filename


EXPORTERS = {
    "txt": TxtExporter,
    "xlsx": XlsxExporter,
    "pdf": PdfExporter,
}


def get_exporter(fmt: str) -> Exporter:
    """Фабрика: возвращает экспортёр по названию формата.

    Args:
        fmt: Название формата (например, 'pdf', 'xlsx').

    Returns:
        Экземпляр класса экспортёра.

    Raises:
        ValueError: Если формат не поддерживается.
    """
    exporter_class = EXPORTERS.get(fmt.lower())
    if not exporter_class:
        raise ValueError(f"Неизвестный формат отчёта: {fmt}")
    return exporter_class()
