import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, pagination, require_roles
from app.core.exceptions import NotFoundException
from app.models.alert import Alert
from app.models.recording import Recording
from app.models.report import Report
from app.models.task import Task
from app.models.user import User
from app.schemas.common import PageData, ResponseModel
from app.schemas.report import RecordingOut, ReportDetail, ReportListItem
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["报告中心"])


class ReportGenerateRequest(BaseModel):
    task_id: str | None = None


@router.get("", response_model=ResponseModel[PageData[ReportListItem]], summary="报告列表")
async def list_reports(
    pager: dict = Depends(pagination),
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    result = await report_service.get_list(db, current_user.tenant_id, pager["page"], pager["size"])
    return ResponseModel.ok(data=result)


@router.get("/{report_id}", response_model=ResponseModel[ReportDetail], summary="报告详情")
async def get_report(
    report_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    report = await report_service.get_by_id(db, report_id, current_user.tenant_id)
    timeline = await report_service.get_timeline(db, report_id)
    snapshots = await report_service.get_snapshots(db, report_id)

    detail = ReportDetail.model_validate(report)
    detail.timeline = timeline
    detail.snapshots = snapshots
    return ResponseModel.ok(data=detail)


@router.post("/generate", response_model=ResponseModel, summary="生成报告")
async def generate_report(
    body: ReportGenerateRequest,
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    task: Task | None = None
    if body.task_id:
        task_result = await db.execute(
            select(Task).where(Task.id == body.task_id, Task.tenant_id == current_user.tenant_id)
        )
        task = task_result.scalar_one_or_none()
        if not task:
            raise NotFoundException("任务不存在")
    else:
        task_result = await db.execute(
            select(Task)
            .where(Task.tenant_id == current_user.tenant_id)
            .order_by(Task.completed_at.desc().nullslast(), Task.scheduled_at.desc())
            .limit(1)
        )
        task = task_result.scalar_one_or_none()
        if not task:
            raise NotFoundException("暂无可生成报告的任务")

    existing = await db.execute(
        select(Report).where(Report.task_id == task.id, Report.tenant_id == current_user.tenant_id)
    )
    report = existing.scalar_one_or_none()
    if report:
        return ResponseModel.ok(
            message="报告已存在，返回已有报告",
            data={"report_id": report.id, "task_id": report.task_id, "created_at": report.created_at.isoformat()},
        )

    alerts_count_result = await db.execute(
        select(func.count()).where(Alert.tenant_id == current_user.tenant_id, Alert.task_id == task.id)
    )
    alert_count = int(alerts_count_result.scalar_one() or 0)

    duration_min = 15
    if task.started_at and task.completed_at and task.completed_at > task.started_at:
        duration_min = max(1, int((task.completed_at - task.started_at).total_seconds() // 60))

    report_id = f"rep_{uuid.uuid4().hex[:10]}"
    report = Report(
        id=report_id,
        tenant_id=current_user.tenant_id,
        task_id=task.id,
        drone_id=task.drone_id,
        flight_duration_min=duration_min,
        flight_distance_km=Decimal(max(0.5, duration_min / 12)).quantize(Decimal("0.01")),
        vehicle_count=10 + alert_count * 2,
        pedestrian_count=20 + alert_count,
        alert_count=alert_count,
        peak_congestion_index=Decimal(min(0.99, 0.30 + alert_count * 0.05)).quantize(Decimal("0.01")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(report)

    record_result = await db.execute(
        select(Recording)
        .where(Recording.tenant_id == current_user.tenant_id, Recording.task_id == task.id)
        .order_by(Recording.start_at.desc())
        .limit(1)
    )
    latest_recording = record_result.scalar_one_or_none()
    if latest_recording:
        latest_recording.report_id = report_id

    await db.flush()
    return ResponseModel.ok(
        message="报告生成成功",
        data={"report_id": report_id, "task_id": task.id},
    )


@router.get("/{report_id}/trajectory", response_model=ResponseModel, summary="获取飞行轨迹")
async def get_trajectory(
    report_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    await report_service.get_by_id(db, report_id, current_user.tenant_id)
    trajectory = await report_service.get_trajectory(db, report_id)
    return ResponseModel.ok(
        data=[
            {
                "longitude": float(t.longitude),
                "latitude": float(t.latitude),
                "altitude": float(t.altitude) if t.altitude else None,
                "recorded_at": t.recorded_at.isoformat(),
            }
            for t in trajectory
        ]
    )


@router.get("/recordings/list", response_model=ResponseModel[PageData[RecordingOut]], summary="录像列表")
async def list_recordings(
    task_id: str | None = Query(None),
    pager: dict = Depends(pagination),
    current_user: User = Depends(require_roles("enterprise_admin", "analyst", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    result = await report_service.get_recordings(db, current_user.tenant_id, pager["page"], pager["size"], task_id)
    return ResponseModel.ok(data=result)
