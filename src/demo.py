from datetime import date, time

from src import PawsApp
from src import AuthManager
from src import Role


def seed_demo_data(app: PawsApp, auth: AuthManager) -> None:
    """Загружает демо-данные, если в базе ещё нет сотрудников.

    5 сотрудников, каждому — пользователь со своей ролью, и две смены.
    """
    if app.list_employees():
        return

    demo = [
        ("Иванов Иван Иванович", "Оператор", "ivanov", "admin123", Role.ADMIN),
        ("Петров Пётр Петрович", "Оператор", "petrov", "manager123", Role.MANAGER),
        (
            "Сидорова Анна Сергеевна",
            "Старший оператор",
            "sidorova",
            "worker123",
            Role.EMPLOYEE,
        ),
        (
            "Кузнецов Дмитрий Алексеевич",
            "Кладовщик",
            "kuznetsov",
            "store123",
            Role.EMPLOYEE,
        ),
        (
            "Смирнова Ольга Викторовна",
            "Бухгалтер",
            "smirnova",
            "budget123",
            Role.MANAGER,
        ),
    ]
    employees = []
    for full_name, position, username, password, role in demo:
        employee = app.add_employee(full_name, position)
        auth.add_user(username, password, employee.id, role)
        employees.append(employee)

    app.add_shift(
        employees[0].id,
        date.today(),
        time(8, 0),
        time(20, 0),
        "Приём заказов",
    )
    app.add_shift(
        employees[1].id,
        date.today(),
        time(20, 0),
        time(8, 0),
        "Ночная смена, склад",
    )
    print(f"Демо-данные загружены: {len(demo)} сотрудников, {len(demo)} пользователей")
    print("Демо-учётные записи (логин / пароль / роль):")
    for _, _, username, password, role in demo:
        print(f"  {username} / {password} / {role.value}")
