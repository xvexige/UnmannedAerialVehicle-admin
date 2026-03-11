import json
import logging
import random
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.drone import Drone
from app.models.task import Task
from app.models.alert import Alert
from app.models.user import User
from app.schemas.dashboard import DashboardOverview

logger = logging.getLogger("drone.api")


async def get_overview(db: AsyncSession, tenant_id: str) -> DashboardOverview:
    # 尝试从 Redis 取缓存
    cache_key = f"dashboard:overview:{tenant_id}"
    try:
        from app.db.redis import get_redis
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return DashboardOverview(**json.loads(cached))
    except Exception:
        redis = None
        logger.warning("Redis 不可用，跳过大屏缓存")

    today_start = datetime.combine(date.today(), datetime.min.time())

    total_drones = (await db.execute(
        select(func.count()).where(Drone.tenant_id == tenant_id)
    )).scalar_one()

    online_drones = (await db.execute(
        select(func.count()).where(
            Drone.tenant_id == tenant_id,
            Drone.status.in_(["online", "in_task"])
        )
    )).scalar_one()

    total_tasks_today = (await db.execute(
        select(func.count()).where(
            Task.tenant_id == tenant_id,
            Task.scheduled_at >= today_start,
        )
    )).scalar_one()

    unread_alerts = (await db.execute(
        select(func.count()).where(
            Alert.tenant_id == tenant_id,
            Alert.status == "unread",
        )
    )).scalar_one()

    overview = DashboardOverview(
        total_flights_today=total_tasks_today,
        online_drones=online_drones,
        offline_drones=total_drones - online_drones,
        total_drones=total_drones,
        total_detections_today=0,
        unread_alerts=unread_alerts,
        total_tasks_today=total_tasks_today,
    )

    # 写入缓存（可选）
    try:
        if redis:
            await redis.setex(cache_key, 60, json.dumps(overview.model_dump()))
    except Exception:
        pass

    return overview


async def get_map_drones(db: AsyncSession, tenant_id: str) -> list[dict]:
    result = await db.execute(
        select(Drone).where(Drone.tenant_id == tenant_id)
    )
    drones = result.scalars().all()

    return [
        {
            "id": d.id,
            "name": d.name,
            "status": d.status,
            "longitude": float(d.longitude) if d.longitude else None,
            "latitude": float(d.latitude) if d.latitude else None,
            "battery_level": d.battery_level,
            "pilot_name": None,
        }
        for d in drones
    ]


async def get_traffic_trend(db: AsyncSession, tenant_id: str) -> list[dict]:
    """返回过去24小时每小时车流量趋势（模拟数据）"""
    now = datetime.utcnow()
    trend = []
    for i in range(24, 0, -1):
        hour = (now - timedelta(hours=i)).strftime("%H:00")
        is_peak = int(hour[:2]) in [7, 8, 9, 17, 18, 19]
        base = 300 if is_peak else 100
        trend.append({
            "hour": hour,
            "vehicle_count": base + random.randint(-20, 50),
            "pedestrian_count": (base // 3) + random.randint(-5, 15),
        })
    return trend
