class Storage:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj.employees = {}
            obj.shifts = {}
            obj._employee_counter = 0
            obj._shift_counter = 0
            cls._instance = obj
        return cls._instance

    def next_employee_id(self) -> int:
        self._employee_counter += 1
        return self._employee_counter

    def next_shift_id(self) -> int:
        self._shift_counter += 1
        return self._shift_counter