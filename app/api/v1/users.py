from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles, pagination
from app.schemas.common import ResponseModel, PageData
from app.schemas.user import UserCreate, UserUpdate, UserDetail, UserListItem, InviteCodeCreate, InviteCodeOut
from app.services import user_service
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=ResponseModel[PageData[UserListItem]], summary="用户列表")
async def list_users(
    role: str | None = Query(None),
    pager: dict = Depends(pagination),
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    result = await user_service.get_list(db, current_user.tenant_id, pager["page"], pager["size"], role)
    return ResponseModel.ok(data=result)


@router.get("/{user_id}", response_model=ResponseModel[UserDetail], summary="用户详情")
async def get_user(
    user_id: str,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    user = await user_service.get_by_id(db, user_id, current_user.tenant_id)
    return ResponseModel.ok(data=UserDetail.model_validate(user))


@router.post("", response_model=ResponseModel[UserListItem], summary="创建员工账号")
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    user = await user_service.create_user(db, current_user.tenant_id, body)
    return ResponseModel.ok(data=UserListItem.model_validate(user), message="员工账号创建成功")


@router.put("/{user_id}", response_model=ResponseModel[UserListItem], summary="更新用户信息")
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    user = await user_service.update_user(db, user_id, current_user.tenant_id, body)
    return ResponseModel.ok(data=UserListItem.model_validate(user))


@router.delete("/{user_id}", response_model=ResponseModel, summary="删除员工账号")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    await user_service.delete_user(db, user_id, current_user.tenant_id)
    return ResponseModel.ok(message="员工账号已删除")


@router.post("/invite-codes", response_model=ResponseModel[InviteCodeOut], summary="生成邀请码")
async def create_invite_code(
    body: InviteCodeCreate,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    invite = await user_service.create_invite_code(
        db, current_user.tenant_id, current_user.id, body.role, body.expire_hours
    )
    return ResponseModel.ok(data=InviteCodeOut.model_validate(invite), message="邀请码已生成")
