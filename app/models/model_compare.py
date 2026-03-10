from datetime import datetime
from sqlalchemy import String, DateTime, Enum, DECIMAL, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from decimal import Decimal


class ModelCompareJob(Base):
    __tablename__ = "model_compare_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False)
    model_a_id: Mapped[str] = mapped_column(String(32), nullable=False)
    model_b_id: Mapped[str] = mapped_column(String(32), nullable=False)
    video_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(
        Enum("pending", "processing", "completed", "failed"),
        nullable=False, default="pending"
    )
    result_a_map50: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    result_a_miss_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    result_a_fps: Mapped[int | None] = mapped_column(SmallInteger)
    result_a_video_url: Mapped[str | None] = mapped_column(String(512))
    result_b_map50: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    result_b_miss_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    result_b_fps: Mapped[int | None] = mapped_column(SmallInteger)
    result_b_video_url: Mapped[str | None] = mapped_column(String(512))
    miss_rate_improvement: Mapped[str | None] = mapped_column(String(16))
    map50_improvement: Mapped[str | None] = mapped_column(String(16))
    created_by: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
