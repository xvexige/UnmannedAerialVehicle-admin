from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class AlertListItem(BaseModel):
    id: str
    type: str
    description: str | None
    level: str
    status: str
    drone_id: str | None
    task_id: str | None
    snapshot_url: str | None
    triggered_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertDetail(AlertListItem):
    tenant_id: str
    longitude: Decimal | None
    latitude: Decimal | None
    video_clip_url: str | None
    object_type: str | None
    confidence: Decimal | None
    bbox_x: int | None
    bbox_y: int | None
    bbox_width: int | None
    bbox_height: int | None
    resolved_by: str | None
    resolved_at: datetime | None
    remark: str | None


class AlertResolve(BaseModel):
    remark: str | None = None


class AlertCreate(BaseModel):
    type: str
    description: str | None = None
    level: str = "warning"
    drone_id: str | None = None
    task_id: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    snapshot_url: str | None = None
    object_type: str | None = None
    confidence: float | None = None
    bbox_x: int | None = None
    bbox_y: int | None = None
    bbox_width: int | None = None
    bbox_height: int | None = None
    triggered_at: datetime | None = None
