from datetime import datetime
from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str
    code: str
    admin_email: str
    phone: str | None = None
    address: str | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class TenantListItem(BaseModel):
    id: str
    name: str
    code: str
    admin_email: str
    phone: str | None
    status: str
    plan_id: str | None
    expire_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantDetail(TenantListItem):
    address: str | None
    freeze_reason: str | None


class TenantFreezeRequest(BaseModel):
    reason: str
