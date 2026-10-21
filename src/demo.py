from datetime import date, time

from src.app import PawsApp
from src.auth import AuthManager
from src.models import Role


def seed_demo_data(app: PawsApp, auth: AuthManager) -> None:
    """Загружает демо-данные: 5 сотрудников, каждому — пользователь со своей ролью."""
    demo = [
        ("Иванов Иван Иванович", "Оператор", "ivanov", "admin123", Role.ADMIN),
        ("Петров Пётр Петрович", "Оператор", "petrov", "manager123", Role.MANAGER),
        ("Сидорова Анна Сергеевна", "Старший оператор", "sidorova", "worker123", Role.EMPLOYEE),
        ("Кузнецов Дмитрий Алексеевич", "Кладовщик", "kuznetsov", "store123", Role.EMPLOYEE),
        ("Смирнова Ольга Викторовна", "Бухгалтер", "smirnova", "budget123", Role.MANAGER),
    ]
    for full_name, position, username, password, role in demo:
        employee = app.add_employee(full_name, position)
        auth.add_user(username, password, employee.id, role)

    app.add_shift(app.list_employees()[0].id, date.today(),
                  time(8, 0), time(20, 0), "Приём заказов")
    app.add_shift(app.list_employees()[1].id, date.today(),
                  time(20, 0), time(8, 0), "Ночная смена, склад")
    print(f"Демо-данные загружены: {len(demo)} сотрудников, {len(demo)} пользователей")
