from datetime import date, time

from app import PawsApp
from report import calculate_duration


def seed_demo_data(app: PawsApp) -> None:
    ivanov = app.add_employee("Иванов Иван Иванович", "Оператор")
    petrov = app.add_employee("Петров Пётр Петрович", "Оператор")
    app.add_shift(ivanov["id"], date.today(), time(8, 0), time(20, 0), "Приём заказов")
    app.add_shift(petrov["id"], date.today(), time(20, 0), time(8, 0), "Ночная смена, склад")
    print(f"Демо-данные загружены: {ivanov['full_name']} (id={ivanov['id']}), "
          f"{petrov['full_name']} (id={petrov['id']})")


def read_date(prompt: str) -> date:
    return date.fromisoformat(input(prompt).strip())


def read_time(prompt: str) -> time:
    return time.fromisoformat(input(prompt).strip())


MENU = """
==== PAWS - учёт рабочих смен ====
1. Добавить сотрудника
2. Показать список сотрудников
3. Добавить смену
4. Показать смены сотрудника
5. Сформировать и сохранить отчёт
0. Выход
Выберите пункт: """


def main():
    app = PawsApp()
    seed_demo_data(app)

    while True:
        choice = input(MENU).strip()
        try:
            match choice:
                case "1":
                    name = input("ФИО сотрудника: ").strip()
                    position = input("Должность: ").strip()
                    employee = app.add_employee(name, position)
                    print(f"Добавлен сотрудник: {employee['full_name']} (id={employee['id']})")

                case "2":
                    for e in app.list_employees():
                        print(f"  id={e['id']}: {e['full_name']} ({e['position']})")

                case "3":
                    employee_id = int(input("ID сотрудника: ").strip())
                    shift_date = read_date("Дата смены (ГГГГ-ММ-ДД): ")
                    start = read_time("Начало (ЧЧ:ММ): ")
                    end = read_time("Окончание (ЧЧ:ММ): ")
                    description = input("Описание выполненных работ: ").strip()
                    shift = app.add_shift(employee_id, shift_date, start, end, description)
                    print(f"Смена добавлена (id={shift['id']}, "
                          f"{calculate_duration(shift)} ч.)")

                case "4":
                    employee_id = int(input("ID сотрудника: ").strip())
                    shifts = app.list_shifts(employee_id)
                    if not shifts:
                        print("Смен не найдено")
                    for s in shifts:
                        print(f"  {s['date']} {s['start']}-{s['end']} "
                              f"({calculate_duration(s)} ч.) - {s['description']}")

                case "5":
                    date_from = read_date("Период с (ГГГГ-ММ-ДД): ")
                    date_to = read_date("Период по (ГГГГ-ММ-ДД): ")
                    emp_input = input("ID сотрудника (пусто - по всем сотрудникам): ").strip()
                    employee_id = int(emp_input) if emp_input else None
                    report = app.generate_report(date_from, date_to, employee_id)
                    print(report["text"])
                    fmt = input("Формат сохранения (txt/csv): ").strip() or "txt"
                    filename = f"report.{fmt}"
                    app.export_report(report, fmt, filename)
                    print(f"Отчёт сохранён в файл: {filename}")

                case "0":
                    print("До свидания!")
                    break

                case "_":
                    print("Неизвестный пункт меню, попробуйте снова")

        except Exception as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()