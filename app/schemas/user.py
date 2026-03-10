from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: str
    phone: str | None = None
    email: str | None = None
    role: str


class UserUpdate(BaseModel):
    real_name: str | None = None
    phone: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    role: str | None = None
    status: str | None = None


class UserListItem(BaseModel):
    id: str
    username: str
    real_name: str
    phone: str | None
    email: str | None
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserDetail(UserListItem):
    tenant_id: str | None
    avatar_url: str | None


class InviteCodeCreate(BaseModel):
    role: str
    expire_hours: int = 72


class InviteCodeOut(BaseModel):
    code: str
    role: str
    expire_at: datetime

    model_config = {"from_attributes": True}
