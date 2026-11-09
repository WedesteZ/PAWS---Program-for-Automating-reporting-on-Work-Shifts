import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class CompletedWorkOrm(Base):
    """Выполненная работа в рамках смены."""

    __tablename__ = "completed_works"
    __table_args__ = (
        CheckConstraint(
            "description <> ''", name="completed_works_description_check"
        ),
        Index("completed_works_shift_idx", "shift_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shifts.id", ondelete="CASCADE")
    )
    description: Mapped[str] = mapped_column(String(500))
    work_date: Mapped[date | None]
    details: Mapped[str | None] = mapped_column(String(500))

    shift: Mapped["ShiftOrm"] = relationship(back_populates="works")


class EmployeeOrm(Base):
    """Сотрудник."""

    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("full_name <> ''", name="employees_name_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    full_name: Mapped[str] = mapped_column(String(150))
    position: Mapped[str] = mapped_column(String(50))
    department: Mapped[str | None] = mapped_column(String(100))
    hire_date: Mapped[date] = mapped_column(server_default=func.current_date())
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    shifts: Mapped[list["ShiftOrm"]] = relationship(back_populates="employee")
    user: Mapped["UserOrm | None"] = relationship(
        back_populates="employee", uselist=False
    )


class ReportEmployeeOrm(Base):
    """Связь отчёта с сотрудником (отчёт по группе сотрудников)."""

    __tablename__ = "report_employees"
    __table_args__ = (
        Index("report_employees_employee_idx", "employee_id"),
    )

    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), primary_key=True
    )


class ReportOrm(Base):
    """Отчёт за период."""

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "file_format IN ('pdf', 'xlsx', 'txt', 'csv')",
            name="reports_format_check",
        ),
        CheckConstraint(
            "date_from <= date_to",
            name="reports_period_check",
        ),
        CheckConstraint(
            "report_type IN ('daily', 'summary')",
            name="reports_type_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    report_type: Mapped[str] = mapped_column(String(20))
    date_from: Mapped[date]
    date_to: Mapped[date]
    file_format: Mapped[str | None] = mapped_column(String(10))
    file_path: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )

    employees: Mapped[list["EmployeeOrm"]] = relationship(
        secondary="report_employees"
    )


class SettingOrm(Base):
    """Настройки."""

    __tablename__ = "settings"

    setting_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    setting_value: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ShiftOrm(Base):
    """Смена сотрудника."""

    __tablename__ = "shifts"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="shifts_time_check"),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'closed')",
            name="shifts_status_check",
        ),
        Index("shifts_employee_start_idx", "employee_id", "start_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT")
    )
    start_at: Mapped[datetime]
    end_at: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    employee: Mapped["EmployeeOrm"] = relationship(back_populates="shifts")
    works: Mapped[list["CompletedWorkOrm"]] = relationship(
        back_populates="shift",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserOrm(Base):
    """Учётная запись пользователя."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "user_role IN ('admin', 'manager', 'employee')",
            name="users_role_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    login: Mapped[str] = mapped_column(String(30), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    user_role: Mapped[str] = mapped_column(String(20))
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        unique=True,
    )

    employee: Mapped["EmployeeOrm"] = relationship(back_populates="user")
    