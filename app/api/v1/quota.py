from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, require_roles
from app.schemas.common import ResponseModel, PageData
from app.schemas.quota import QuotaOut, QuotaUsageLogOut
from app.models.quota import Quota, QuotaUsageLog
from app.models.user import User

router = APIRouter(prefix="/quota", tags=["额度管理"])


@router.get("/current", response_model=ResponseModel[QuotaOut], summary="当前账期额度")
async def current_quota(
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst"""
    from datetime import date
    from app.core.exceptions import NotFoundException

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
        if quota.video_hours_total > 0 else 0
    )
    data.storage_gb_percent = (
        round(float(quota.storage_gb_used) / quota.storage_gb_total * 100, 1)
        if quota.storage_gb_total > 0 else 0
    )
    data.api_calls_percent = (
        round(quota.api_calls_used / quota.api_calls_total * 100, 1)
        if quota.api_calls_total > 0 else 0
    )
    return ResponseModel.ok(data=data)


@router.get("/usage-logs", response_model=ResponseModel[PageData[QuotaUsageLogOut]], summary="额度消耗明细")
async def usage_logs(
    type: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst"""
    stmt = select(QuotaUsageLog).where(QuotaUsageLog.tenant_id == current_user.tenant_id)
    if type:
        stmt = stmt.where(QuotaUsageLog.type == type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(QuotaUsageLog.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()

    return ResponseModel.ok(data=PageData(
        total=total, page=page, size=size,
        list=[QuotaUsageLogOut.model_validate(r) for r in rows]
    ))
