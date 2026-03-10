from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.common import ResponseModel
from app.schemas.auth import (
    LoginRequest, RefreshTokenRequest, RegisterRequest,
    RegisterByInviteRequest, ChangePasswordRequest, TokenData
)
from app.services import auth_service
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ResponseModel[TokenData], summary="用户登录")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """[权限] 无需登录"""
    data = await auth_service.login(db, body.username, body.password, body.tenant_code)
    return ResponseModel.ok(data=data, message="登录成功")


@router.post("/refresh", response_model=ResponseModel, summary="刷新 Token")
async def refresh(body: RefreshTokenRequest):
    """[权限] 无需登录"""
    data = await auth_service.refresh_access_token(body.refresh_token)
    return ResponseModel.ok(data=data, message="刷新成功")


@router.post("/logout", response_model=ResponseModel, summary="退出登录")
async def logout(current_user: User = Depends(get_current_user), request: Request = None):
    """[权限] 所有登录用户"""
    from jose import jwt
    from app.config import settings
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    await auth_service.logout(payload["jti"], payload["exp"])
    return ResponseModel.ok(message="已退出登录")


@router.post("/register", response_model=ResponseModel, summary="企业注册")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """[权限] 无需登录，创建企业管理员账号"""
    data = await auth_service.register_enterprise(db, body)
    return ResponseModel.ok(data=data, message="注册成功")


@router.post("/register-by-invite", response_model=ResponseModel, summary="通过邀请码注册")
async def register_by_invite(body: RegisterByInviteRequest, db: AsyncSession = Depends(get_db)):
    """[权限] 无需登录，通过邀请码注册为企业员工"""
    data = await auth_service.register_by_invite(db, body)
    return ResponseModel.ok(data=data, message="注册成功")


@router.put("/password", response_model=ResponseModel, summary="修改密码")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[权限] 所有登录用户"""
    await auth_service.change_password(db, current_user, body.old_password, body.new_password)
    return ResponseModel.ok(message="密码修改成功")


@router.get("/me", response_model=ResponseModel, summary="获取当前用户信息")
async def me(current_user: User = Depends(get_current_user)):
    """[权限] 所有登录用户"""
    return ResponseModel.ok(data={
        "id": current_user.id,
        "username": current_user.username,
        "real_name": current_user.real_name,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "avatar_url": current_user.avatar_url,
        "status": current_user.status,
        "last_login_at": current_user.last_login_at,
    })
