from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.drone import Drone
from app.models.task import Task
from app.models.alert import Alert
from app.models.telemetry import DroneTelemetrySnapshot
from app.models.user import User
from app.schemas.dashboard import DashboardOverview, DroneMapItem
from app.db.redis import get_redis


async def get_overview(db: AsyncSession, tenant_id: str) -> DashboardOverview:
    redis = await get_redis()
    cache_key = f"dashboard:overview:{tenant_id}"
    import json

    cached = await redis.get(cache_key)
    if cached:
        return DashboardOverview(**json.loads(cached))

    today_start = datetime.combine(date.today(), datetime.min.time())

    total_drones_r = await db.execute(
        select(func.count()).where(Drone.tenant_id == tenant_id)
    )
    total_drones = total_drones_r.scalar_one()

    online_r = await db.execute(
        select(func.count()).where(
            Drone.tenant_id == tenant_id,
            Drone.status.in_(["online", "in_task"])
        )
    )
    online_drones = online_r.scalar_one()

    tasks_today_r = await db.execute(
        select(func.count()).where(
            Task.tenant_id == tenant_id,
            Task.scheduled_at >= today_start
        )
    )
    total_tasks_today = tasks_today_r.scalar_one()

    unread_r = await db.execute(
        select(func.count()).where(
            Alert.tenant_id == tenant_id,
            Alert.status == "unread"
        )
    )
    unread_alerts = unread_r.scalar_one()

    overview = DashboardOverview(
        total_flights_today=total_tasks_today,
        online_drones=online_drones,
        offline_drones=total_drones - online_drones,
        total_drones=total_drones,
        total_detections_today=0,
        unread_alerts=unread_alerts,
        total_tasks_today=total_tasks_today,
    )

    await redis.setex(cache_key, 60, json.dumps(overview.model_dump()))
    return overview


async def get_map_drones(db: AsyncSession, tenant_id: str) -> list[dict]:
    result = await db.execute(
        select(Drone, User).join(User, User.id == Drone.current_task_id, isouter=True)
        .where(Drone.tenant_id == tenant_id)
    )
    rows = result.all()

    items = []
    for row in rows:
        drone = row[0]
        items.append({
            "id": drone.id,
            "name": drone.name,
            "status": drone.status,
            "longitude": float(drone.longitude) if drone.longitude else None,
            "latitude": float(drone.latitude) if drone.latitude else None,
            "battery_level": drone.battery_level,
            "pilot_name": None,
        })
    return items


async def get_traffic_trend(db: AsyncSession, tenant_id: str) -> list[dict]:
    """返回过去24小时每小时车流量趋势（模拟数据，实际从检测日志聚合）"""
    from datetime import timedelta
    import random
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
