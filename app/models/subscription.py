from datetime import datetime
from sqlalchemy import String, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(32), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(
        Enum("active", "expired", "cancelled"), nullable=False, default="active"
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
