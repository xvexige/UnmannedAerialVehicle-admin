from datetime import datetime
from sqlalchemy import String, DateTime, Enum, Integer, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("illegal_parking", "congestion", "intrusion", "other"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(512))
    level: Mapped[str] = mapped_column(
        Enum("info", "warning", "critical"), nullable=False, default="warning"
    )
    status: Mapped[str] = mapped_column(
        Enum("unread", "read", "resolved"), nullable=False, default="unread"
    )
    drone_id: Mapped[str | None] = mapped_column(String(32))
    task_id: Mapped[str | None] = mapped_column(String(32))
    longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(11, 7))
    latitude: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 7))
    snapshot_url: Mapped[str | None] = mapped_column(String(512))
    video_clip_url: Mapped[str | None] = mapped_column(String(512))
    object_type: Mapped[str | None] = mapped_column(String(32))
    confidence: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    bbox_x: Mapped[int | None] = mapped_column(Integer)
    bbox_y: Mapped[int | None] = mapped_column(Integer)
    bbox_width: Mapped[int | None] = mapped_column(Integer)
    bbox_height: Mapped[int | None] = mapped_column(Integer)
    resolved_by: Mapped[str | None] = mapped_column(String(32))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    remark: Mapped[str | None] = mapped_column(String(512))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
