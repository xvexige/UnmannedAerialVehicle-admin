import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.alert import Alert
from app.core.exceptions import NotFoundException
from app.schemas.alert import AlertCreate
from app.schemas.common import PageData


async def get_list(
    db: AsyncSession,
    tenant_id: str,
    page: int,
    size: int,
    status: str | None = None,
    level: str | None = None,
    alert_type: str | None = None,
) -> PageData:
    stmt = select(Alert).where(Alert.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Alert.status == status)
    if level:
        stmt = stmt.where(Alert.level == level)
    if alert_type:
        stmt = stmt.where(Alert.type == alert_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Alert.triggered_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return PageData(total=total, page=page, size=size, list=list(rows))


async def get_by_id(db: AsyncSession, alert_id: str, tenant_id: str) -> Alert:
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.tenant_id == tenant_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundException("?????")
    return alert


async def create_alert(db: AsyncSession, tenant_id: str, data: AlertCreate) -> Alert:
    alert_id = f"alt_{uuid.uuid4().hex[:10]}"
    alert = Alert(
        id=alert_id,
        tenant_id=tenant_id,
        type=data.type,
        description=data.description,
        level=data.level,
        status="unread",
        drone_id=data.drone_id,
        task_id=data.task_id,
        longitude=data.longitude,
        latitude=data.latitude,
        snapshot_url=data.snapshot_url,
        object_type=data.object_type,
        confidence=data.confidence,
        bbox_x=data.bbox_x,
        bbox_y=data.bbox_y,
        bbox_width=data.bbox_width,
        bbox_height=data.bbox_height,
        triggered_at=data.triggered_at or datetime.utcnow(),
    )
    db.add(alert)
    await db.commit()

    try:
        from app.db.redis import get_redis
        redis = await get_redis()
        await redis.publish("alerts", json.dumps({
            "channel": "alerts",
            "tenant_id": tenant_id,
            "alert_id": alert_id,
            "type": data.type,
            "level": data.level,
            "description": data.description,
            "snapshot_url": data.snapshot_url,
            "triggered_at": alert.triggered_at.isoformat(),
        }))
    except Exception:
        import logging
        logging.getLogger("drone.api").warning("Redis ???????")

    return alert


async def mark_read(db: AsyncSession, alert_id: str, tenant_id: str) -> Alert:
    alert = await get_by_id(db, alert_id, tenant_id)
    if alert.status == "unread":
        alert.status = "read"
    await db.commit()
    return alert


async def resolve_alert(db: AsyncSession, alert_id: str, tenant_id: str, resolver_id: str, remark: str | None) -> Alert:
    alert = await get_by_id(db, alert_id, tenant_id)
    alert.status = "resolved"
    alert.resolved_by = resolver_id
    alert.resolved_at = datetime.utcnow()
    alert.remark = remark
    await db.commit()
    return alert


async def batch_read(db: AsyncSession, tenant_id: str, alert_ids: list[str]):
    await db.execute(
        update(Alert)
        .where(Alert.tenant_id == tenant_id, Alert.id.in_(alert_ids))
        .values(status="read")
    )


async def count_unread(db: AsyncSession, tenant_id: str) -> int:
    result = await db.execute(
        select(func.count()).where(Alert.tenant_id == tenant_id, Alert.status == "unread")
    )
    return result.scalar_one()
