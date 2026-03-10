from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class AIModelOut(BaseModel):
    id: str
    name: str
    version: str
    scene: str
    description: str | None
    map50: Decimal | None
    map75: Decimal | None
    recall: Decimal | None
    precision_score: Decimal | None
    fps: int | None
    miss_rate: Decimal | None
    size_mb: Decimal | None
    is_default: bool
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelCompareJobCreate(BaseModel):
    model_a_id: str
    model_b_id: str
    video_url: str | None = None


class ModelCompareJobOut(BaseModel):
    id: str
    model_a_id: str
    model_b_id: str
    status: str
    result_a_map50: Decimal | None
    result_a_miss_rate: Decimal | None
    result_a_fps: int | None
    result_a_video_url: str | None
    result_b_map50: Decimal | None
    result_b_miss_rate: Decimal | None
    result_b_fps: int | None
    result_b_video_url: str | None
    miss_rate_improvement: str | None
    map50_improvement: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
