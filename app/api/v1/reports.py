from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles, pagination
from app.schemas.common import ResponseModel, PageData
from app.schemas.report import ReportListItem, ReportDetail, RecordingOut
from app.services import report_service
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["报告中心"])


@router.get("", response_model=ResponseModel[PageData[ReportListItem]], summary="报告列表")
async def list_reports(
    pager: dict = Depends(pagination),
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst / pilot"""
    result = await report_service.get_list(db, current_user.tenant_id, pager["page"], pager["size"])
    return ResponseModel.ok(data=result)


@router.get("/{report_id}", response_model=ResponseModel[ReportDetail], summary="报告详情")
async def get_report(
    report_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst / pilot"""
    report = await report_service.get_by_id(db, report_id, current_user.tenant_id)
    timeline = await report_service.get_timeline(db, report_id)
    snapshots = await report_service.get_snapshots(db, report_id)

    detail = ReportDetail.model_validate(report)
    detail.timeline = timeline
    detail.snapshots = snapshots
    return ResponseModel.ok(data=detail)


@router.get("/{report_id}/trajectory", response_model=ResponseModel, summary="获取飞行轨迹")
async def get_trajectory(
    report_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst / pilot"""
    await report_service.get_by_id(db, report_id, current_user.tenant_id)
    trajectory = await report_service.get_trajectory(db, report_id)
    return ResponseModel.ok(data=[{
        "longitude": float(t.longitude),
        "latitude": float(t.latitude),
        "altitude": float(t.altitude) if t.altitude else None,
        "recorded_at": t.recorded_at.isoformat(),
    } for t in trajectory])


@router.get("/recordings/list", response_model=ResponseModel[PageData[RecordingOut]], summary="录像列表")
async def list_recordings(
    task_id: str | None = Query(None),
    pager: dict = Depends(pagination),
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst / pilot"""
    result = await report_service.get_recordings(db, current_user.tenant_id, pager["page"], pager["size"], task_id)
    return ResponseModel.ok(data=result)
