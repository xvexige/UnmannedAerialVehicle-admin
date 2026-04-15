import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.core.exceptions import NotFoundException, ParamException
from app.models.operation_log import OperationLog
from app.models.quota import Quota, QuotaUsageLog
from app.models.user import User
from app.schemas.common import PageData, ResponseModel
from app.schemas.quota import QuotaOut, QuotaUsageLogOut

router = APIRouter(prefix="/quota", tags=["额度管理"])


class QuotaExpansionApplyRequest(BaseModel):
    video_hours: int = Field(0, ge=0, le=5000)
    storage_gb: int = Field(0, ge=0, le=5000)
    api_calls: int = Field(0, ge=0, le=10_000_000)
    reason: str | None = None


@router.get("/current", response_model=ResponseModel[QuotaOut], summary="当前账期额度")
async def current_quota(
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date

    result = await db.execute(
        select(Quota)
        .where(
            Quota.tenant_id == current_user.tenant_id,
            Quota.billing_cycle_start <= date.today(),
            Quota.billing_cycle_end >= date.today(),
        )
        .order_by(Quota.billing_cycle_start.desc())
        .limit(1)
    )
    quota = result.scalar_one_or_none()
    if not quota:
        raise NotFoundException("当前账期额度记录不存在")

    data = QuotaOut.model_validate(quota)
    data.video_hours_percent = (
        round(float(quota.video_hours_used) / quota.video_hours_total * 100, 1)
        if quota.video_hours_total > 0
        else 0
    )
    data.storage_gb_percent = (
        round(float(quota.storage_gb_used) / quota.storage_gb_total * 100, 1)
        if quota.storage_gb_total > 0
        else 0
    )
    data.api_calls_percent = (
        round(quota.api_calls_used / quota.api_calls_total * 100, 1)
        if quota.api_calls_total > 0
        else 0
    )
    return ResponseModel.ok(data=data)


@router.post("/apply-expansion", response_model=ResponseModel, summary="申请扩容")
async def apply_expansion(
    body: QuotaExpansionApplyRequest,
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    if body.video_hours <= 0 and body.storage_gb <= 0 and body.api_calls <= 0:
        raise ParamException("请至少填写一个扩容申请项")

    ticket_id = f"qe_{uuid.uuid4().hex[:10]}"
    log = OperationLog(
        tenant_id=current_user.tenant_id,
        operator_id=current_user.id,
        operator_role=current_user.role,
        action="quota_expansion_apply",
        target_type="quota",
        target_id=None,
        detail={
            "ticket_id": ticket_id,
            "requested": {
                "video_hours": body.video_hours,
                "storage_gb": body.storage_gb,
                "api_calls": body.api_calls,
            },
            "reason": body.reason,
        },
        ip_address=None,
    )
    db.add(log)
    await db.flush()

    return ResponseModel.ok(
        message="扩容申请已提交",
        data={
            "ticket_id": ticket_id,
            "video_hours": body.video_hours,
            "storage_gb": body.storage_gb,
            "api_calls": body.api_calls,
        },
    )


@router.get("/usage-logs", response_model=ResponseModel[PageData[QuotaUsageLogOut]], summary="额度消耗明细")
async def usage_logs(
    type: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(QuotaUsageLog).where(QuotaUsageLog.tenant_id == current_user.tenant_id)
    if type:
        stmt = stmt.where(QuotaUsageLog.type == type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(QuotaUsageLog.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()

    return ResponseModel.ok(
        data=PageData(
            total=total,
            page=page,
            size=size,
            list=[QuotaUsageLogOut.model_validate(r) for r in rows],
        )
    )
