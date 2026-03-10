from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class QuotaOut(BaseModel):
    id: int
    tenant_id: str
    billing_cycle_start: date
    billing_cycle_end: date
    video_hours_total: int
    video_hours_used: Decimal
    storage_gb_total: int
    storage_gb_used: Decimal
    api_calls_total: int
    api_calls_used: int
    alert_threshold_percent: int
    video_hours_percent: float
    storage_gb_percent: float
    api_calls_percent: float
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuotaUsageLogOut(BaseModel):
    id: int
    type: str
    amount: Decimal
    description: str | None
    task_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
