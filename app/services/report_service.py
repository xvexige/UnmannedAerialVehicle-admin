from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.report import Report, ReportTimeline, ReportSnapshot, ReportTrajectory
from app.models.recording import Recording
from app.core.exceptions import NotFoundException
from app.schemas.common import PageData


async def get_list(
    db: AsyncSession, tenant_id: str, page: int, size: int
) -> PageData:
    stmt = select(Report).where(Report.tenant_id == tenant_id)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Report.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return PageData(total=total, page=page, size=size, list=list(rows))


async def get_by_id(db: AsyncSession, report_id: str, tenant_id: str) -> Report:
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.tenant_id == tenant_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("报告不存在")
    return report


async def get_timeline(db: AsyncSession, report_id: str) -> list[ReportTimeline]:
    result = await db.execute(
        select(ReportTimeline).where(ReportTimeline.report_id == report_id)
        .order_by(ReportTimeline.time_point)
    )
    return list(result.scalars().all())


async def get_snapshots(db: AsyncSession, report_id: str) -> list[ReportSnapshot]:
    result = await db.execute(
        select(ReportSnapshot).where(ReportSnapshot.report_id == report_id)
        .order_by(ReportSnapshot.captured_at)
    )
    return list(result.scalars().all())


async def get_trajectory(db: AsyncSession, report_id: str) -> list[ReportTrajectory]:
    result = await db.execute(
        select(ReportTrajectory).where(ReportTrajectory.report_id == report_id)
        .order_by(ReportTrajectory.recorded_at)
    )
    return list(result.scalars().all())


async def get_recordings(
    db: AsyncSession, tenant_id: str, page: int, size: int, task_id: str | None = None
) -> PageData:
    stmt = select(Recording).where(Recording.tenant_id == tenant_id)
    if task_id:
        stmt = stmt.where(Recording.task_id == task_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Recording.start_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return PageData(total=total, page=page, size=size, list=list(rows))
