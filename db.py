from models import Employee, Shift, User


class Storage:
    """Хранилище данных приложения (синглтон).

    Хранит сотрудников, смены и пользователей в памяти
    в словарях, ключами служат их ID/username.
    """

    _instance: "Storage | None" = None

    def __new__(cls) -> "Storage":
        if cls._instance is None:
            obj = super().__new__(cls)
            obj.employees: dict[str, Employee] = {}
            obj.shifts: dict[str, Shift] = {}
            obj.users: dict[str, User] = {}
            cls._instance = obj
        return cls._instance

    def add_employee(self, employee: Employee) -> Employee:
        """Сохраняет сотрудника в хранилище и возвращает его."""
        self.employees[employee.id] = employee
        return employee

    def add_shift(self, shift: Shift) -> Shift:
        """Сохраняет смену в хранилище и возвращает её."""
        self.shifts[shift.id] = shift
        return shift

    def add_user(self, user: User) -> User:
        """Сохраняет пользователя в хранилище и возвращает его."""
        self.users[user.username] = user
        return user
