import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User
from app.models.tenant import Tenant
from app.models.invite_code import InviteCode
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthException, NotFoundException, DuplicateException, ParamException
from app.db.redis import get_redis
from app.schemas.auth import RegisterRequest, RegisterByInviteRequest
from app.config import settings


async def login(db: AsyncSession, username: str, password: str, tenant_code: str | None):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise AuthException("用户名或密码错误")

    if user.status != "active":
        raise AuthException("账号已被禁用，请联系管理员")

    if user.role != "super_admin":
        if not tenant_code:
            raise ParamException("企业账号登录需要提供企业编码")
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.code == tenant_code)
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant or tenant.id != user.tenant_id:
            raise AuthException("企业编码不匹配")
        if tenant.status == "frozen":
            raise AuthException("企业账号已被冻结")

    access_token, access_jti = create_access_token(
        subject=user.id,
        extra={"role": user.role, "tenant_id": user.tenant_id}
    )
    refresh_token, _ = create_refresh_token(subject=user.id)

    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.utcnow())
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "avatar_url": user.avatar_url,
        }
    }


async def refresh_access_token(refresh_token: str):
    from jose import JWTError
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise AuthException("Refresh Token 无效或已过期")

    if payload.get("type") != "refresh":
        raise AuthException("Token 类型错误")

    user_id = payload.get("sub")
    access_token, _ = create_access_token(subject=user_id)
    return {
        "access_token": access_token,
        "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    }


async def logout(jti: str, exp: int):
    try:
        redis = await get_redis()
        ttl = max(exp - int(datetime.now(timezone.utc).timestamp()), 1)
        await redis.setex(f"token:blacklist:{jti}", ttl, "1")
    except Exception:
        import logging
        logging.getLogger("drone.api").warning("Redis 不可用，logout Token 黑名单写入跳过")


async def register_enterprise(db: AsyncSession, data: RegisterRequest):
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise DuplicateException("该用户名已被注册")

    existing_code = await db.execute(select(Tenant).where(Tenant.code == data.tenant_code))
    if existing_code.scalar_one_or_none():
        raise DuplicateException("企业编码已存在")

    tenant_id = f"t_{uuid.uuid4().hex[:12]}"
    tenant = Tenant(
        id=tenant_id,
        name=data.tenant_name,
        code=data.tenant_code,
        admin_email=data.username,
        phone=data.phone,
        status="active",
    )
    db.add(tenant)

    user_id = f"u_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        username=data.username,
        real_name=data.real_name,
        phone=data.phone,
        email=data.username if "@" in data.username else None,
        password_hash=get_password_hash(data.password),
        role="enterprise_admin",
        status="active",
    )
    db.add(user)
    await db.commit()

    return {"tenant_id": tenant_id, "user_id": user_id}


async def register_by_invite(db: AsyncSession, data: RegisterByInviteRequest):
    result = await db.execute(
        select(InviteCode).where(InviteCode.code == data.invite_code)
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise NotFoundException("邀请码不存在")
    if invite.used_by:
        raise ParamException("邀请码已被使用")
    if invite.expire_at < datetime.utcnow():
        raise ParamException("邀请码已过期")

    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise DuplicateException("该用户名已被注册")

    user_id = f"u_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        tenant_id=invite.tenant_id,
        username=data.username,
        real_name=data.real_name,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        role=invite.role,
        status="active",
    )
    db.add(user)

    invite.used_by = user_id
    invite.used_at = datetime.utcnow()
    await db.commit()

    return {"user_id": user_id}


async def change_password(db: AsyncSession, user: User, old_password: str, new_password: str):
    if not verify_password(old_password, user.password_hash):
        raise AuthException("原密码错误")
    new_hash = get_password_hash(new_password)
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(password_hash=new_hash)
    )
    # FastAPI yield 依赖的 commit 在响应发送后才执行，
    # 密码变更需要立即提交，否则下一个登录请求看不到新密码
    await db.commit()
