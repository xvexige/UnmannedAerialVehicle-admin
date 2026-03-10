from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import asyncio

from app.api.deps import get_db, require_roles
from app.schemas.common import ResponseModel
from app.models.drone import Drone
from app.models.user import User
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/monitor", tags=["实时监控"])


@router.get("/{drone_id}/stream-info", response_model=ResponseModel, summary="获取视频流信息")
async def get_stream_info(
    drone_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    result = await db.execute(
        select(Drone).where(Drone.id == drone_id, Drone.tenant_id == current_user.tenant_id)
    )
    drone = result.scalar_one_or_none()
    if not drone:
        raise NotFoundException("无人机不存在")

    return ResponseModel.ok(data={
        "drone_id": drone.id,
        "stream_url": drone.stream_url,
        "hls_url": f"/hls/{drone_id}/index.m3u8",
        "status": drone.status,
    })


@router.get("/{drone_id}/telemetry/latest", response_model=ResponseModel, summary="获取最新遥测数据")
async def get_latest_telemetry(
    drone_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    from app.db.redis import get_redis
    redis = await get_redis()
    cached = await redis.get(f"drone:location:{drone_id}")
    if cached:
        return ResponseModel.ok(data=json.loads(cached))

    from app.models.telemetry import DroneTelemetrySnapshot
    result = await db.execute(
        select(DroneTelemetrySnapshot)
        .where(
            DroneTelemetrySnapshot.drone_id == drone_id,
            DroneTelemetrySnapshot.tenant_id == current_user.tenant_id,
        )
        .order_by(DroneTelemetrySnapshot.recorded_at.desc())
        .limit(1)
    )
    snap = result.scalar_one_or_none()
    if not snap:
        raise NotFoundException("暂无遥测数据")

    return ResponseModel.ok(data={
        "drone_id": snap.drone_id,
        "battery_level": snap.battery_level,
        "speed_ms": float(snap.speed_ms) if snap.speed_ms else None,
        "altitude": float(snap.altitude) if snap.altitude else None,
        "longitude": float(snap.longitude) if snap.longitude else None,
        "latitude": float(snap.latitude) if snap.latitude else None,
        "signal_strength": snap.signal_strength,
        "recorded_at": snap.recorded_at.isoformat(),
    })


@router.get("/{drone_id}/telemetry/history", response_model=ResponseModel, summary="遥测历史（过去N条）")
async def telemetry_history(
    drone_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    from app.models.telemetry import DroneTelemetrySnapshot
    result = await db.execute(
        select(DroneTelemetrySnapshot)
        .where(
            DroneTelemetrySnapshot.drone_id == drone_id,
            DroneTelemetrySnapshot.tenant_id == current_user.tenant_id,
        )
        .order_by(DroneTelemetrySnapshot.recorded_at.desc())
        .limit(limit)
    )
    snaps = result.scalars().all()
    return ResponseModel.ok(data=[{
        "battery_level": s.battery_level,
        "speed_ms": float(s.speed_ms) if s.speed_ms else None,
        "altitude": float(s.altitude) if s.altitude else None,
        "longitude": float(s.longitude) if s.longitude else None,
        "latitude": float(s.latitude) if s.latitude else None,
        "recorded_at": s.recorded_at.isoformat(),
    } for s in reversed(snaps)])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket 实时推送端点
    订阅消息格式：{"action": "subscribe", "channel": "drone_telemetry"|"alerts", "drone_id": "..."}
    """
    from app.core.security import decode_token
    from jose import JWTError
    from app.db.redis import get_redis

    try:
        payload = decode_token(token)
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            await websocket.close(code=4001, reason="Token 无效")
            return
    except JWTError:
        await websocket.close(code=4001, reason="Token 无效")
        return

    await websocket.accept()
    redis = await get_redis()
    subscribed_channels: set[str] = set()

    async def redis_listener():
        pubsub = redis.pubsub()
        await pubsub.subscribe("telemetry", "alerts", "detections")
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    if data.get("tenant_id") == tenant_id:
                        await websocket.send_json(data)
                except Exception:
                    pass
        finally:
            await pubsub.unsubscribe()
            await pubsub.aclose()

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("action") == "ping":
                await websocket.send_json({"action": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        listener_task.cancel()
