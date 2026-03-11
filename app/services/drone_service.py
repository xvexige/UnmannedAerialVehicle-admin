import uuid
import hashlib
import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.drone import Drone
from app.models.telemetry import DroneTelemetrySnapshot
from app.core.exceptions import NotFoundException, DuplicateException, ParamException
from app.schemas.drone import DroneCreate, DroneUpdate, DroneListItem, HeartbeatRequest
from app.schemas.common import PageData
from app.db.redis import get_redis

logger = logging.getLogger("drone.api")


async def get_list(
    db: AsyncSession, tenant_id: str, page: int, size: int, status: str | None = None
) -> PageData[DroneListItem]:
    redis = await get_redis()
    cache_key = f"drones:{tenant_id}:{page}:{size}:{status or 'all'}"
    try:
        if await redis.exists(cache_key):
            cached = await redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return PageData[DroneListItem].model_validate(data)
    except Exception as e:
        logger.error(f"Redis read error: {e}")

    stmt = select(Drone).where(Drone.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Drone.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Drone.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    result = PageData(
        total=total, page=page, size=size, list=[DroneListItem.model_validate(r) for r in rows]
    )

    try:
        await redis.setex(cache_key, 60, result.model_dump_json())
    except Exception as e:
        logger.error(f"Redis write error: {e}")

    return result


async def get_by_id(db: AsyncSession, drone_id: str, tenant_id: str) -> Drone:
    result = await db.execute(
        select(Drone).where(Drone.id == drone_id, Drone.tenant_id == tenant_id)
    )
    drone = result.scalar_one_or_none()
    if not drone:
        raise NotFoundException("??????")
    return drone


async def create(db: AsyncSession, tenant_id: str, data: DroneCreate) -> Drone:
    existing = await db.execute(
        select(Drone).where(Drone.tenant_id == tenant_id, Drone.sn == data.sn)
    )
    if existing.scalar_one_or_none():
        raise DuplicateException("???SN????")

    drone_id = f"d_{uuid.uuid4().hex[:12]}"
    secret_hash = hashlib.sha256(data.secret_key.encode()).hexdigest()[:64]

    drone = Drone(
        id=drone_id,
        tenant_id=tenant_id,
        name=data.name,
        sn=data.sn,
        model=data.model,
        secret_key=secret_hash,
        compute_mode=data.compute_mode,
        edge_node_id=data.edge_node_id,
        status="offline",
    )
    db.add(drone)
    await db.commit()

    # 清除缓存
    try:
        redis = await get_redis()
        keys = await redis.keys(f"drones:{tenant_id}:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        logger.error(f"Redis cache clear error: {e}")

    return drone


async def update_drone(db: AsyncSession, drone_id: str, tenant_id: str, data: DroneUpdate) -> Drone:
    drone = await get_by_id(db, drone_id, tenant_id)
    update_data = data.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(drone, key, val)
    await db.commit()

    # 清除缓存
    try:
        redis = await get_redis()
        keys = await redis.keys(f"drones:{tenant_id}:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        logger.error(f"Redis cache clear error: {e}")

    return drone


async def delete_drone(db: AsyncSession, drone_id: str, tenant_id: str):
    from sqlalchemy.exc import IntegrityError
    drone = await get_by_id(db, drone_id, tenant_id)
    try:
        await db.delete(drone)
        await db.commit()

        # 清除缓存
        redis = await get_redis()
        keys = await redis.keys(f"drones:{tenant_id}:*")
        if keys:
            await redis.delete(*keys)

    except IntegrityError:
        await db.rollback()
        raise ParamException("?????????????????????????")
    except Exception as e:
        logger.error(f"Redis cache clear error: {e}")


async def heartbeat(db: AsyncSession, data: HeartbeatRequest, tenant_id: str):
    result = await db.execute(
        select(Drone).where(Drone.id == data.drone_id, Drone.tenant_id == tenant_id)
    )
    drone = result.scalar_one_or_none()
    if not drone:
        raise NotFoundException("??????")

    now = datetime.utcnow()
    update_vals: dict = {"last_heartbeat_at": now}
    if drone.status == "offline":
        update_vals["status"] = "online"

    for field in ["battery_level", "longitude", "latitude", "altitude"]:
        val = getattr(data, field, None)
        if val is not None:
            update_vals[field] = val

    await db.execute(update(Drone).where(Drone.id == data.drone_id).values(**update_vals))

    snapshot = DroneTelemetrySnapshot(
        drone_id=data.drone_id,
        tenant_id=tenant_id,
        battery_level=data.battery_level,
        speed_ms=data.speed_ms,
        altitude=data.altitude,
        longitude=data.longitude,
        latitude=data.latitude,
        signal_strength=data.signal_strength,
        temperature_celsius=data.temperature_celsius,
        recorded_at=now,
    )
    db.add(snapshot)
    await db.commit()

    try:
        from app.db.redis import get_redis
        redis = await get_redis()
        loc = {
            "drone_id": data.drone_id,
            "longitude": data.longitude,
            "latitude": data.latitude,
            "altitude": data.altitude,
            "battery_level": data.battery_level,
            "recorded_at": now.isoformat(),
        }
        await redis.setex(f"drone:location:{data.drone_id}", 60, json.dumps(loc))
        await redis.publish("telemetry", json.dumps({
            "channel": "telemetry",
            "tenant_id": tenant_id,
            **loc,
        }))
    except Exception:
        logger.warning("Redis ???????????????")


async def get_map_drones(db: AsyncSession, tenant_id: str) -> list[Drone]:
    result = await db.execute(
        select(Drone).where(
            Drone.tenant_id == tenant_id,
            Drone.status.in_(["online", "in_task"])
        )
    )
    return list(result.scalars().all())
