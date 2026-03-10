from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_db, require_roles
from app.schemas.common import ResponseModel, PageData
from app.schemas.alert import AlertDetail, AlertListItem, AlertCreate, AlertResolve
from app.services import alert_service
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["告警管理"])


@router.get("", response_model=ResponseModel[PageData[AlertListItem]], summary="告警列表")
async def list_alerts(
    status: str | None = Query(None),
    level: str | None = Query(None),
    type: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    result = await alert_service.get_list(db, current_user.tenant_id, page, size, status, level, type)
    return ResponseModel.ok(data=result)


@router.get("/count/unread", response_model=ResponseModel, summary="未读告警数量")
async def unread_count(
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    count = await alert_service.count_unread(db, current_user.tenant_id)
    return ResponseModel.ok(data={"count": count})


@router.get("/{alert_id}", response_model=ResponseModel[AlertDetail], summary="告警详情")
async def get_alert(
    alert_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    alert = await alert_service.get_by_id(db, alert_id, current_user.tenant_id)
    await alert_service.mark_read(db, alert_id, current_user.tenant_id)
    return ResponseModel.ok(data=AlertDetail.model_validate(alert))


@router.post("", response_model=ResponseModel[AlertListItem], summary="创建告警（AI服务内部调用）")
async def create_alert(
    body: AlertCreate,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot（AI推理服务内部调用）"""
    alert = await alert_service.create_alert(db, current_user.tenant_id, body)
    return ResponseModel.ok(data=AlertListItem.model_validate(alert), message="告警已创建")


@router.patch("/{alert_id}/resolve", response_model=ResponseModel, summary="处理告警")
async def resolve_alert(
    alert_id: str,
    body: AlertResolve,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot"""
    await alert_service.resolve_alert(db, alert_id, current_user.tenant_id, current_user.id, body.remark)
    return ResponseModel.ok(message="告警已处理")


class BatchReadRequest(BaseModel):
    alert_ids: list[str]


@router.post("/batch/read", response_model=ResponseModel, summary="批量标记已读")
async def batch_read(
    body: BatchReadRequest,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    await alert_service.batch_read(db, current_user.tenant_id, body.alert_ids)
    return ResponseModel.ok(message="已标记为已读")
