from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.schemas.common import ResponseModel
from app.services import dashboard_service
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["数据大屏"])


@router.get("/overview", response_model=ResponseModel, summary="大屏概览统计")
async def overview(
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    data = await dashboard_service.get_overview(db, current_user.tenant_id)
    return ResponseModel.ok(data=data)


@router.get("/drones/map", response_model=ResponseModel, summary="地图上所有无人机位置")
async def drones_map(
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    items = await dashboard_service.get_map_drones(db, current_user.tenant_id)
    return ResponseModel.ok(data=items)


@router.get("/traffic/trend", response_model=ResponseModel, summary="过去24小时交通流量趋势")
async def traffic_trend(
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    trend = await dashboard_service.get_traffic_trend(db, current_user.tenant_id)
    return ResponseModel.ok(data=trend)
