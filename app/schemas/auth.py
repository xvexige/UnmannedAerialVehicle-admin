from pydantic import BaseModel, field_validator
import re


class LoginRequest(BaseModel):
    username: str
    password: str
    tenant_code: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    real_name: str
    phone: str | None = None
    tenant_name: str
    tenant_code: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度不得少于8位")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含数字")
        return v


class RegisterByInviteRequest(BaseModel):
    invite_code: str
    username: str
    password: str
    real_name: str
    phone: str | None = None


class UserInfo(BaseModel):
    id: str
    username: str
    real_name: str
    role: str
    tenant_id: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserInfo


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
