from datetime import datetime
from sqlalchemy import String, DateTime, Enum, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(Enum("pilot", "analyst"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(32), nullable=False)
    used_by: Mapped[str | None] = mapped_column(String(32))
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
