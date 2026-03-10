from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class WaypointIn(BaseModel):
    seq: int
    longitude: float
    latitude: float
    altitude: float = 100.0


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    drone_id: str
    assignee_id: str
    model_id: str | None = None
    scheduled_at: datetime
    remark: str | None = None
    waypoints: list[WaypointIn] = []


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    drone_id: str | None = None
    assignee_id: str | None = None
    model_id: str | None = None
    scheduled_at: datetime | None = None
    remark: str | None = None
    waypoints: list[WaypointIn] | None = None


class TaskStatusUpdate(BaseModel):
    status: str


class WaypointOut(BaseModel):
    seq: int
    longitude: Decimal
    latitude: Decimal
    altitude: Decimal

    model_config = {"from_attributes": True}


class TaskListItem(BaseModel):
    id: str
    name: str
    drone_id: str
    assignee_id: str
    status: str
    scheduled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskDetail(TaskListItem):
    tenant_id: str
    description: str | None
    model_id: str | None
    remark: str | None
    created_by: str
    waypoints: list[WaypointOut] = []
