import uuid
import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.invite_code import InviteCode
from app.core.exceptions import NotFoundException, DuplicateException
from app.core.security import get_password_hash
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.common import PageData


async def get_list(
    db: AsyncSession, tenant_id: str, page: int, size: int, role: str | None = None
) -> PageData:
    stmt = select(User).where(User.tenant_id == tenant_id)
    if role:
        stmt = stmt.where(User.role == role)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(User.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return PageData(total=total, page=page, size=size, list=list(rows))


async def get_by_id(db: AsyncSession, user_id: str, tenant_id: str) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("用户不存在")
    return user


async def create_user(db: AsyncSession, tenant_id: str, data: UserCreate) -> User:
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise DuplicateException("用户名已存在")

    user_id = f"u_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        username=data.username,
        real_name=data.real_name,
        phone=data.phone,
        email=data.email,
        password_hash=get_password_hash(data.password),
        role=data.role,
        status="active",
    )
    db.add(user)
    await db.flush()
    return user


async def update_user(db: AsyncSession, user_id: str, tenant_id: str, data: UserUpdate) -> User:
    user = await get_by_id(db, user_id, tenant_id)
    update_data = data.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(user, key, val)
    await db.flush()
    return user


async def delete_user(db: AsyncSession, user_id: str, tenant_id: str):
    user = await get_by_id(db, user_id, tenant_id)
    await db.delete(user)
    await db.flush()


async def create_invite_code(
    db: AsyncSession, tenant_id: str, created_by: str, role: str, expire_hours: int
) -> InviteCode:
    code = secrets.token_urlsafe(16)
    invite = InviteCode(
        tenant_id=tenant_id,
        code=code,
        role=role,
        created_by=created_by,
        expire_at=datetime.utcnow() + timedelta(hours=expire_hours),
    )
    db.add(invite)
    await db.flush()
    return invite
