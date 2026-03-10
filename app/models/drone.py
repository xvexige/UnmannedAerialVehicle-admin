from datetime import datetime
from sqlalchemy import String, DateTime, Enum, DECIMAL, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class Drone(Base):
    __tablename__ = "drones"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sn: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(64))
    secret_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("online", "offline", "in_task"), nullable=False, default="offline"
    )
    battery_level: Mapped[int | None] = mapped_column(SmallInteger)
    longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(11, 7))
    latitude: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 7))
    altitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2))
    compute_mode: Mapped[str] = mapped_column(Enum("cloud", "edge"), nullable=False, default="cloud")
    edge_node_id: Mapped[str | None] = mapped_column(String(32))
    current_task_id: Mapped[str | None] = mapped_column(String(32))
    stream_url: Mapped[str | None] = mapped_column(String(512))
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
