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


# 南昌范围内模拟无人机（用于大屏演示与视频识别入口）
NANCHANG_CENTER = (115.858, 28.683)
MOCK_DRONES_NANCHANG = [
    {"id": "sim_nc_1", "name": "南昌-巡逻机1", "status": "online", "longitude": 115.82, "latitude": 28.71, "battery_level": 85, "pilot_name": None, "simulated": True},
    {"id": "sim_nc_2", "name": "南昌-巡逻机2", "status": "in_task", "longitude": 115.90, "latitude": 28.65, "battery_level": 72, "pilot_name": None, "simulated": True},
    {"id": "sim_nc_3", "name": "南昌-巡逻机3", "status": "online", "longitude": 115.88, "latitude": 28.70, "battery_level": 91, "pilot_name": None, "simulated": True},
    {"id": "sim_nc_4", "name": "南昌-巡逻机4", "status": "online", "longitude": 115.84, "latitude": 28.66, "battery_level": 68, "pilot_name": None, "simulated": True},
    {"id": "sim_nc_5", "name": "南昌-巡逻机5", "status": "in_task", "longitude": 115.92, "latitude": 28.68, "battery_level": 78, "pilot_name": None, "simulated": True},
]


async def get_map_drones(db: AsyncSession, tenant_id: str) -> list[dict]:
    result = await db.execute(
        select(Drone).where(Drone.tenant_id == tenant_id)
    )
    drones = result.scalars().all()

    items = [
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
    # 合并南昌范围内模拟无人机，便于大屏演示与点击进行本机视频识别
    for mock in MOCK_DRONES_NANCHANG:
        mock_copy = {**mock, "longitude": mock["longitude"], "latitude": mock["latitude"]}
        items.append(mock_copy)
    return items


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
