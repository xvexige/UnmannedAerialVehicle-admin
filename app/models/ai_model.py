from datetime import datetime
from sqlalchemy import String, DateTime, Enum, SmallInteger, DECIMAL, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    scene: Mapped[str] = mapped_column(
        Enum("highway", "intersection", "night", "bad_weather", "general"),
        nullable=False, default="general"
    )
    description: Mapped[str | None] = mapped_column(String(512))
    map50: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    map75: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    recall: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    precision_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    fps: Mapped[int | None] = mapped_column(SmallInteger)
    miss_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    size_mb: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2))
    file_url: Mapped[str | None] = mapped_column(String(512))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_by: Mapped[str | None] = mapped_column(String(32))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
