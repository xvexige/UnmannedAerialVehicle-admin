from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.db.session import get_db
from app.db.redis import get_redis
from app.core.security import decode_token
from app.core.exceptions import AuthException, PermissionException
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise AuthException("未携带认证 Token")
    try:
        payload = decode_token(token)
    except JWTError:
        raise AuthException("Token 无效或已过期")

    if payload.get("type") != "access":
        raise AuthException("Token 类型错误")

    user_id: str = payload.get("sub")
    if not user_id:
        raise AuthException("Token 数据异常")

    redis = await get_redis()
    jti = payload.get("jti", "")
    if await redis.get(f"token:blacklist:{jti}"):
        raise AuthException("Token 已失效，请重新登录")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or user.status != "active":
        raise AuthException("用户不存在或已被禁用")

    return user


def require_roles(*roles: str):
    """角色权限检查工厂，生成依赖函数"""

    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise PermissionException(
                f"无权限：需要角色 {list(roles)}，当前角色 [{current_user.role}]"
            )
        return current_user

    return checker


def pagination(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)):
    return {"page": page, "size": size}
