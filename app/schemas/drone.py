from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class DroneCreate(BaseModel):
    name: str
    sn: str
    secret_key: str
    model: str | None = None
    compute_mode: str = "cloud"
    edge_node_id: str | None = None


class DroneUpdate(BaseModel):
    name: str | None = None
    model: str | None = None
    compute_mode: str | None = None
    edge_node_id: str | None = None
    stream_url: str | None = None


class DroneListItem(BaseModel):
    id: str
    name: str
    sn: str
    model: str | None
    status: str
    battery_level: int | None
    longitude: Decimal | None
    latitude: Decimal | None
    altitude: Decimal | None
    compute_mode: str
    last_heartbeat_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DroneDetail(DroneListItem):
    tenant_id: str
    stream_url: str | None
    edge_node_id: str | None
    current_task_id: str | None


class TelemetryData(BaseModel):
    drone_id: str
    battery_level: int | None
    speed_ms: Decimal | None
    altitude: Decimal | None
    longitude: Decimal | None
    latitude: Decimal | None
    signal_strength: int | None
    temperature_celsius: Decimal | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class HeartbeatRequest(BaseModel):
    drone_id: str
    battery_level: int | None = None
    speed_ms: float | None = None
    altitude: float | None = None
    longitude: float | None = None
    latitude: float | None = None
    signal_strength: int | None = None
    temperature_celsius: float | None = None
