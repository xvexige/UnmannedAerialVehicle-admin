import uuid
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.drone import Drone
from app.models.telemetry import DroneTelemetrySnapshot
from app.core.exceptions import NotFoundException, DuplicateException, PermissionException
from app.schemas.drone import DroneCreate, DroneUpdate, HeartbeatRequest
from app.schemas.common import PageData


async def get_list(
    db: AsyncSession, tenant_id: str, page: int, size: int, status: str | None = None
) -> PageData:
    stmt = select(Drone).where(Drone.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Drone.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Drone.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()

    return PageData(total=total, page=page, size=size, list=list(rows))


async def get_by_id(db: AsyncSession, drone_id: str, tenant_id: str) -> Drone:
    result = await db.execute(
        select(Drone).where(Drone.id == drone_id, Drone.tenant_id == tenant_id)
    )
    drone = result.scalar_one_or_none()
    if not drone:
        raise NotFoundException("无人机不存在")
    return drone


async def create(db: AsyncSession, tenant_id: str, data: DroneCreate) -> Drone:
    existing = await db.execute(
        select(Drone).where(Drone.tenant_id == tenant_id, Drone.sn == data.sn)
    )
    if existing.scalar_one_or_none():
        raise DuplicateException("该设备SN码已绑定")

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
    await db.flush()
    return drone


async def update_drone(db: AsyncSession, drone_id: str, tenant_id: str, data: DroneUpdate) -> Drone:
    drone = await get_by_id(db, drone_id, tenant_id)
    update_data = data.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(drone, key, val)
    await db.flush()
    return drone


async def delete_drone(db: AsyncSession, drone_id: str, tenant_id: str):
    drone = await get_by_id(db, drone_id, tenant_id)
    await db.delete(drone)
    await db.flush()


async def heartbeat(db: AsyncSession, data: HeartbeatRequest, tenant_id: str):
    result = await db.execute(
        select(Drone).where(Drone.id == data.drone_id, Drone.tenant_id == tenant_id)
    )
    drone = result.scalar_one_or_none()
    if not drone:
        raise NotFoundException("无人机不存在")

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
    await db.flush()

    from app.db.redis import get_redis
    redis = await get_redis()
    import json
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


async def get_map_drones(db: AsyncSession, tenant_id: str) -> list[Drone]:
    result = await db.execute(
        select(Drone).where(
            Drone.tenant_id == tenant_id,
            Drone.status.in_(["online", "in_task"])
        )
    )
    return list(result.scalars().all())
