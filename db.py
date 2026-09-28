from models import Employee, Shift, User


class Storage:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj.employees: dict[str, Employee] = {}
            obj.shifts: dict[str, Shift] = {}
            obj.users: dict[str, User] = {}
            cls._instance = obj
        return cls._instance

    def add_employee(self, employee: Employee) -> Employee:
        self.employees[employee.id] = employee
        return employee

    def add_shift(self, shift: Shift) -> Shift:
        self.shifts[shift.id] = shift
        return shift

    def add_user(self, user: User) -> User:
        self.users[user.username] = user
        return user
