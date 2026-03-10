from datetime import datetime
from sqlalchemy import String, DateTime, Enum, SmallInteger, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class EdgeNode(Base):
    __tablename__ = "edge_nodes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(Enum("cloud", "edge"), nullable=False, default="edge")
    gpu_model: Mapped[str | None] = mapped_column(String(64))
    gpu_usage_percent: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), default=Decimal("0.00"))
    memory_used_gb: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), default=Decimal("0.00"))
    memory_total_gb: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), default=Decimal("0.00"))
    active_streams: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[str] = mapped_column(
        Enum("healthy", "degraded", "offline"), nullable=False, default="offline"
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
