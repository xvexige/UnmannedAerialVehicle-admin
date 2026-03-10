from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles, pagination
from app.schemas.common import ResponseModel, PageData
from app.schemas.drone import DroneCreate, DroneUpdate, DroneDetail, DroneListItem, HeartbeatRequest
from app.services import drone_service
from app.models.user import User

router = APIRouter(prefix="/drones", tags=["无人机管理"])


@router.get("", response_model=ResponseModel[PageData[DroneListItem]], summary="获取无人机列表")
async def list_drones(
    status: str | None = Query(None, description="在线状态过滤"),
    pager: dict = Depends(pagination),
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    result = await drone_service.get_list(db, current_user.tenant_id, pager["page"], pager["size"], status)
    return ResponseModel.ok(data=result)


@router.get("/map", response_model=ResponseModel, summary="获取地图上所有无人机实时位置")
async def map_drones(
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    items = await drone_service.get_map_drones(db, current_user.tenant_id)
    return ResponseModel.ok(data=items)


@router.get("/{drone_id}", response_model=ResponseModel[DroneDetail], summary="获取无人机详情")
async def get_drone(
    drone_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    drone = await drone_service.get_by_id(db, drone_id, current_user.tenant_id)
    return ResponseModel.ok(data=DroneDetail.model_validate(drone))


@router.post("", response_model=ResponseModel[DroneDetail], summary="绑定新无人机")
async def create_drone(
    body: DroneCreate,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    drone = await drone_service.create(db, current_user.tenant_id, body)
    return ResponseModel.ok(data=DroneDetail.model_validate(drone), message="设备绑定成功")


@router.put("/{drone_id}", response_model=ResponseModel[DroneDetail], summary="更新无人机信息")
async def update_drone(
    drone_id: str,
    body: DroneUpdate,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    drone = await drone_service.update_drone(db, drone_id, current_user.tenant_id, body)
    return ResponseModel.ok(data=DroneDetail.model_validate(drone))


@router.delete("/{drone_id}", response_model=ResponseModel, summary="解绑无人机")
async def delete_drone(
    drone_id: str,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    await drone_service.delete_drone(db, drone_id, current_user.tenant_id)
    return ResponseModel.ok(message="设备解绑成功")


@router.post("/heartbeat", response_model=ResponseModel, summary="无人机心跳上报")
async def heartbeat(
    body: HeartbeatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[权限] 所有登录用户（设备端调用）"""
    await drone_service.heartbeat(db, body, current_user.tenant_id)
    return ResponseModel.ok(message="心跳已接收")
