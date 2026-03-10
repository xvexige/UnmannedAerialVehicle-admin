from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Integer, BigInteger, Enum, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class Quota(Base):
    __tablename__ = "quota"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    billing_cycle_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_cycle_end: Mapped[date] = mapped_column(Date, nullable=False)
    video_hours_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    video_hours_used: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal("0.00"))
    storage_gb_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_gb_used: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal("0.00"))
    api_calls_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    api_calls_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alert_threshold_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuotaUsageLog(Base):
    __tablename__ = "quota_usage_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    type: Mapped[str] = mapped_column(Enum("video_hours", "storage_gb", "api_calls"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    task_id: Mapped[str | None] = mapped_column(String(32))
    drone_id: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
