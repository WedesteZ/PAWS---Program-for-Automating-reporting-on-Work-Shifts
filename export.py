import csv

class Exporter:
    def export(self, report: dict, filename: str) -> str:
        raise NotImplementedError


class TxtExporter(Exporter):
    def export(self, report: dict, filename: str) -> str:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report["text"])
        return filename


class CsvExporter(Exporter):
    def export(self, report: dict, filename: str) -> str:
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
    fmt = fmt.strip().lower()
    if fmt == "csv":
        return CsvExporter()
    return TxtExporter()