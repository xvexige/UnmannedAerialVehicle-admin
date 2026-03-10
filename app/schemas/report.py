from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class TimelinePoint(BaseModel):
    time_point: str
    vehicle_count: int
    pedestrian_count: int
    congestion_index: Decimal

    model_config = {"from_attributes": True}


class SnapshotOut(BaseModel):
    snapshot_url: str
    description: str | None
    captured_at: datetime

    model_config = {"from_attributes": True}


class TrajectoryPoint(BaseModel):
    longitude: Decimal
    latitude: Decimal
    altitude: Decimal | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: str
    task_id: str
    drone_id: str
    flight_duration_min: int
    flight_distance_km: Decimal
    vehicle_count: int
    pedestrian_count: int
    alert_count: int
    peak_congestion_index: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportDetail(ReportListItem):
    tenant_id: str
    timeline: list[TimelinePoint] = []
    snapshots: list[SnapshotOut] = []


class RecordingOut(BaseModel):
    id: str
    drone_id: str
    task_id: str | None
    start_at: datetime
    end_at: datetime | None
    duration_min: int
    play_url: str | None
    size_mb: int

    model_config = {"from_attributes": True}
