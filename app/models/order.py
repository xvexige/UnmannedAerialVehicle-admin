from datetime import datetime
from sqlalchemy import String, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    payment_method: Mapped[str] = mapped_column(Enum("alipay", "wechat", "transfer"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "paid", "cancelled", "refunded"), nullable=False, default="pending"
    )
    pay_url: Mapped[str | None] = mapped_column(String(512))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
