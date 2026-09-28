import csv


class Exporter:
    """Базовый класс экспорта отчёта в файл."""

    def export(self, report: dict, filename: str) -> str:
        """Сохраняет отчёт в файл. Возвращает имя файла."""
        raise NotImplementedError


class TxtExporter(Exporter):
    """Экспорт отчёта в текстовый файл."""

    def export(self, report: dict, filename: str) -> str:
        """Сохраняет текстовое представление отчёта. Возвращает имя файла."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report["text"])
        return filename


class CsvExporter(Exporter):
    """Экспорт отчёта в CSV (разделитель ';', кодировка UTF-8 с BOM для Excel)."""

    def export(self, report: dict, filename: str) -> str:
        """Сохраняет таблицу и итоги отчёта. Возвращает имя файла."""
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Сотрудник", "Дата", "Начало", "Конец", "Часы", "Описание"])
            for row in report["rows"]:
                writer.writerow(row)
            writer.writerow([])
            writer.writerow(["Всего смен", report["totals"]["total_shifts"]])
            writer.writerow(["Всего часов", report["totals"]["total_hours"]])
        return filename


def get_exporter(fmt: str) -> Exporter:
    """Возвращает экспортёр для формата fmt (по умолчанию — TXT)."""
    fmt = fmt.strip().lower()
    if fmt == "csv":
        return CsvExporter()
    return TxtExporter()