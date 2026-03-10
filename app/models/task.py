from datetime import datetime
from sqlalchemy import String, DateTime, Enum, Text, BigInteger, SmallInteger, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    drone_id: Mapped[str] = mapped_column(String(32), nullable=False)
    assignee_id: Mapped[str] = mapped_column(String(32), nullable=False)
    model_id: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "completed", "cancelled"),
        nullable=False, default="pending"
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    remark: Mapped[str | None] = mapped_column(String(512))
    created_by: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskWaypoint(Base):
    __tablename__ = "task_waypoints"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(32), nullable=False)
    seq: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    longitude: Mapped[Decimal] = mapped_column(DECIMAL(11, 7), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(DECIMAL(10, 7), nullable=False)
    altitude: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=Decimal("100"))
