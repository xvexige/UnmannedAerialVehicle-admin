from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_roles
from app.schemas.common import ResponseModel
from app.schemas.plan import PlanOut, PlanCreate, PlanUpdate
from app.models.plan import Plan
from app.models.user import User

router = APIRouter(prefix="/plans", tags=["套餐管理"])


@router.get("", response_model=ResponseModel, summary="获取套餐列表")
async def list_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[权限] 所有登录用户"""
    result = await db.execute(
        select(Plan).where(Plan.is_active == True).order_by(Plan.price_monthly)
    )
    plans = result.scalars().all()
    return ResponseModel.ok(data=[PlanOut.model_validate(p) for p in plans])


@router.post("", response_model=ResponseModel[PlanOut], summary="新增套餐")
async def create_plan(
    body: PlanCreate,
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] super_admin"""
    from app.core.exceptions import DuplicateException
    existing = await db.execute(select(Plan).where(Plan.id == body.id))
    if existing.scalar_one_or_none():
        raise DuplicateException("套餐ID已存在")

    plan = Plan(**body.model_dump())
    db.add(plan)
    await db.flush()
    return ResponseModel.ok(data=PlanOut.model_validate(plan), message="套餐已添加")


@router.put("/{plan_id}", response_model=ResponseModel[PlanOut], summary="更新套餐")
async def update_plan(
    plan_id: str,
    body: PlanUpdate,
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] super_admin"""
    from app.core.exceptions import NotFoundException
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise NotFoundException("套餐不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(plan, key, val)
    await db.flush()
    return ResponseModel.ok(data=PlanOut.model_validate(plan))
