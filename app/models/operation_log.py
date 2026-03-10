from datetime import datetime
from sqlalchemy import String, DateTime, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column
from typing import Any
from app.db.session import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str | None] = mapped_column(String(32))
    operator_id: Mapped[str] = mapped_column(String(32), nullable=False)
    operator_role: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(32))
    detail: Mapped[Any | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
