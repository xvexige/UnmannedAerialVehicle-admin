from datetime import datetime, time
from sqlalchemy import String, DateTime, Integer, BigInteger, DECIMAL, Time
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    task_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    drone_id: Mapped[str] = mapped_column(String(32), nullable=False)
    flight_duration_min: Mapped[int] = mapped_column(Integer, default=0)
    flight_distance_km: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), default=Decimal("0.00"))
    vehicle_count: Mapped[int] = mapped_column(Integer, default=0)
    pedestrian_count: Mapped[int] = mapped_column(Integer, default=0)
    alert_count: Mapped[int] = mapped_column(Integer, default=0)
    peak_congestion_index: Mapped[Decimal] = mapped_column(DECIMAL(4, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportTimeline(Base):
    __tablename__ = "report_timeline"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(32), nullable=False)
    time_point: Mapped[time] = mapped_column(Time, nullable=False)
    vehicle_count: Mapped[int] = mapped_column(Integer, default=0)
    pedestrian_count: Mapped[int] = mapped_column(Integer, default=0)
    congestion_index: Mapped[Decimal] = mapped_column(DECIMAL(4, 2), default=Decimal("0.00"))


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ReportTrajectory(Base):
    __tablename__ = "report_trajectory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(32), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(DECIMAL(11, 7), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(DECIMAL(10, 7), nullable=False)
    altitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(3), nullable=False)
