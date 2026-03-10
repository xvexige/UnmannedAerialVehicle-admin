from fastapi import Depends
from app.core.exceptions import PermissionException

ROLE_SUPER_ADMIN = "super_admin"
ROLE_ENTERPRISE_ADMIN = "enterprise_admin"
ROLE_PILOT = "pilot"
ROLE_ANALYST = "analyst"

ALL_ROLES = [ROLE_SUPER_ADMIN, ROLE_ENTERPRISE_ADMIN, ROLE_PILOT, ROLE_ANALYST]
ENTERPRISE_ROLES = [ROLE_ENTERPRISE_ADMIN, ROLE_PILOT, ROLE_ANALYST]


def require_roles(*roles: str):
    """
    角色权限检查工厂函数，在路由中使用：
    Depends(require_roles("super_admin", "enterprise_admin"))
    """
    from app.api.deps import get_current_user

    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise PermissionException(f"当前角色 [{current_user.role}] 无权限访问，需要角色: {list(roles)}")
        return current_user

    return checker
