from pydantic import BaseModel
from decimal import Decimal


class DashboardOverview(BaseModel):
    total_flights_today: int
    online_drones: int
    offline_drones: int
    total_drones: int
    total_detections_today: int
    unread_alerts: int
    total_tasks_today: int


class DroneMapItem(BaseModel):
    id: str
    name: str
    status: str
    longitude: Decimal | None
    latitude: Decimal | None
    battery_level: int | None
    pilot_name: str | None

    model_config = {"from_attributes": True}


class TrafficTrendPoint(BaseModel):
    hour: str
    vehicle_count: int
    pedestrian_count: int


class PlatformStats(BaseModel):
    total_tenants: int
    active_tenants: int
    total_concurrent_streams: int
    total_api_calls_today: int
    gpu_usage_percent: Decimal | None
