from datetime import datetime
from pydantic import BaseModel


class PlanCreate(BaseModel):
    id: str
    name: str
    price_monthly: int
    max_drones: int = 5
    video_hours_monthly: int = 200
    storage_gb: int = 100
    night_detection: bool = False
    edge_computing: bool = False
    support_level: str = "工单支持"
    description: str | None = None


class PlanUpdate(BaseModel):
    name: str | None = None
    price_monthly: int | None = None
    max_drones: int | None = None
    video_hours_monthly: int | None = None
    storage_gb: int | None = None
    night_detection: bool | None = None
    edge_computing: bool | None = None
    support_level: str | None = None
    description: str | None = None
    is_active: bool | None = None


class PlanOut(BaseModel):
    id: str
    name: str
    price_monthly: int
    max_drones: int
    video_hours_monthly: int
    storage_gb: int
    night_detection: bool
    edge_computing: bool
    support_level: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
