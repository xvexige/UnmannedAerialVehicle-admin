from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    price_monthly: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_drones: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    video_hours_monthly: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    storage_gb: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    night_detection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    edge_computing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    support_level: Mapped[str] = mapped_column(String(32), nullable=False, default="工单支持")
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
