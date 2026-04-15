import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.exceptions import DuplicateException, NotFoundException
from app.models.operation_log import OperationLog
from app.models.order import Order
from app.models.plan import Plan
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate

router = APIRouter(prefix="/plans", tags=["套餐管理"])


class ContactSalesRequest(BaseModel):
    plan_id: str | None = None
    duration_months: int = Field(1, ge=1, le=36)
    remark: str | None = None


@router.get("", response_model=ResponseModel, summary="获取套餐列表")
async def list_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.price_monthly))
    plans = result.scalars().all()
    return ResponseModel.ok(data=[PlanOut.model_validate(p) for p in plans])


@router.post("/contact-sales", response_model=ResponseModel, summary="联系销售")
async def contact_sales(
    body: ContactSalesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan: Plan | None = None
    if body.plan_id:
        result = await db.execute(select(Plan).where(Plan.id == body.plan_id, Plan.is_active == True))
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundException("套餐不存在")
    else:
        result = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.price_monthly).limit(1))
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundException("暂无可用套餐")

    order_id = f"ord_{uuid.uuid4().hex[:10]}"
    amount = plan.price_monthly * body.duration_months
    order = Order(
        id=order_id,
        tenant_id=current_user.tenant_id,
        plan_id=plan.id,
        duration_months=body.duration_months,
        amount=amount,
        currency="CNY",
        payment_method="transfer",
        status="pending",
        pay_url=None,
        paid_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(order)

    ticket_id = f"sales_{uuid.uuid4().hex[:10]}"
    db.add(
        OperationLog(
            tenant_id=current_user.tenant_id,
            operator_id=current_user.id,
            operator_role=current_user.role,
            action="contact_sales",
            target_type="plan",
            target_id=plan.id,
            detail={
                "ticket_id": ticket_id,
                "order_id": order_id,
                "duration_months": body.duration_months,
                "remark": body.remark,
            },
            ip_address=None,
        )
    )
    await db.flush()

    return ResponseModel.ok(
        message="销售咨询已提交",
        data={
            "ticket_id": ticket_id,
            "order_id": order_id,
            "plan_id": plan.id,
            "amount": amount,
            "currency": "CNY",
        },
    )


@router.post("", response_model=ResponseModel[PlanOut], summary="新增套餐")
async def create_plan(
    body: PlanCreate,
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Plan).where(Plan.id == body.id))
    if existing.scalar_one_or_none():
        raise DuplicateException("套餐ID已存在")

    plan = Plan(**body.model_dump())
    db.add(plan)
    await db.flush()
    return ResponseModel.ok(data=PlanOut.model_validate(plan), message="套餐已新增")


@router.put("/{plan_id}", response_model=ResponseModel[PlanOut], summary="更新套餐")
async def update_plan(
    plan_id: str,
    body: PlanUpdate,
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise NotFoundException("套餐不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(plan, key, val)
    await db.flush()
    return ResponseModel.ok(data=PlanOut.model_validate(plan))
