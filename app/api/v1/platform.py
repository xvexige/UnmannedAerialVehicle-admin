from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.api.deps import get_db, require_roles
from app.schemas.common import ResponseModel, PageData
from app.schemas.tenant import TenantListItem, TenantDetail, TenantFreezeRequest
from app.models.tenant import Tenant
from app.models.user import User
from app.models.drone import Drone
from app.models.edge_node import EdgeNode
from datetime import datetime

router = APIRouter(prefix="/platform", tags=["平台超管"])


@router.get("/tenants", response_model=ResponseModel[PageData[TenantListItem]], summary="所有租户列表")
async def list_tenants(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] super_admin"""
    stmt = select(Tenant)
    if status:
        stmt = stmt.where(Tenant.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Tenant.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()

    return ResponseModel.ok(data=PageData(
        total=total, page=page, size=size,
        list=[TenantListItem.model_validate(r) for r in rows]
    ))


@router.get("/tenants/{tenant_id}", response_model=ResponseModel[TenantDetail], summary="租户详情")
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] super_admin"""
    from app.core.exceptions import NotFoundException
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise NotFoundException("租户不存在")
    return ResponseModel.ok(data=TenantDetail.model_validate(tenant))


@router.post("/tenants/{tenant_id}/freeze", response_model=ResponseModel, summary="冻结租户")
async def freeze_tenant(
    tenant_id: str,
    body: TenantFreezeRequest,
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] super_admin"""
    await db.execute(
        update(Tenant).where(Tenant.id == tenant_id).values(
            status="frozen", freeze_reason=body.reason
        )
    )
    return ResponseModel.ok(message="租户已冻结")


@router.post("/tenants/{tenant_id}/unfreeze", response_model=ResponseModel, summary="解冻租户")
async def unfreeze_tenant(
    tenant_id: str,
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] super_admin"""
    await db.execute(
        update(Tenant).where(Tenant.id == tenant_id).values(
            status="active", freeze_reason=None
        )
    )
    return ResponseModel.ok(message="租户已解冻")


@router.get("/stats", response_model=ResponseModel, summary="平台宏观统计")
async def platform_stats(
    current_user: User = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] super_admin"""
    total_tenants = (await db.execute(select(func.count()).select_from(Tenant))).scalar_one()
    active_tenants = (await db.execute(
        select(func.count()).where(Tenant.status == "active")
    )).scalar_one()
    total_drones = (await db.execute(select(func.count()).select_from(Drone))).scalar_one()
    online_drones = (await db.execute(
        select(func.count()).where(Drone.status.in_(["online", "in_task"]))
    )).scalar_one()

    node_result = await db.execute(
        select(func.avg(EdgeNode.gpu_usage_percent)).where(EdgeNode.status == "healthy")
    )
    avg_gpu = node_result.scalar_one()

    return ResponseModel.ok(data={
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_drones": total_drones,
        "online_drones": online_drones,
        "avg_gpu_usage_percent": float(avg_gpu) if avg_gpu else 0,
        "total_concurrent_streams": online_drones,
    })
