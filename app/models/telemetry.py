from datetime import datetime
from sqlalchemy import String, DateTime, BigInteger, SmallInteger, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class DroneTelemetrySnapshot(Base):
    __tablename__ = "drone_telemetry_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drone_id: Mapped[str] = mapped_column(String(32), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    battery_level: Mapped[int | None] = mapped_column(SmallInteger)
    speed_ms: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 2))
    altitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2))
    longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(11, 7))
    latitude: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 7))
    signal_strength: Mapped[int | None] = mapped_column(SmallInteger)
    temperature_celsius: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(3), nullable=False)
