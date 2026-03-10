import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete

from app.models.task import Task, TaskWaypoint
from app.models.drone import Drone
from app.core.exceptions import NotFoundException, ParamException
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate
from app.schemas.common import PageData


async def get_list(
    db: AsyncSession,
    tenant_id: str,
    page: int,
    size: int,
    status: str | None = None,
    assignee_id: str | None = None,
) -> PageData:
    stmt = select(Task).where(Task.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Task.status == status)
    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Task.scheduled_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return PageData(total=total, page=page, size=size, list=list(rows))


async def get_by_id(db: AsyncSession, task_id: str, tenant_id: str) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.tenant_id == tenant_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException("任务不存在")
    return task


async def get_waypoints(db: AsyncSession, task_id: str) -> list[TaskWaypoint]:
    result = await db.execute(
        select(TaskWaypoint).where(TaskWaypoint.task_id == task_id).order_by(TaskWaypoint.seq)
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, tenant_id: str, created_by: str, data: TaskCreate) -> Task:
    drone_result = await db.execute(
        select(Drone).where(Drone.id == data.drone_id, Drone.tenant_id == tenant_id)
    )
    if not drone_result.scalar_one_or_none():
        raise NotFoundException("指定无人机不存在")

    task_id = f"task_{uuid.uuid4().hex[:10]}"
    task = Task(
        id=task_id,
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        drone_id=data.drone_id,
        assignee_id=data.assignee_id,
        model_id=data.model_id,
        scheduled_at=data.scheduled_at,
        remark=data.remark,
        created_by=created_by,
        status="pending",
    )
    db.add(task)
    await db.flush()

    for wp in data.waypoints:
        waypoint = TaskWaypoint(
            task_id=task_id,
            seq=wp.seq,
            longitude=wp.longitude,
            latitude=wp.latitude,
            altitude=wp.altitude,
        )
        db.add(waypoint)

    await db.flush()
    return task


async def update_task(db: AsyncSession, task_id: str, tenant_id: str, data: TaskUpdate) -> Task:
    task = await get_by_id(db, task_id, tenant_id)
    if task.status in ("completed", "cancelled"):
        raise ParamException("已完成或已取消的任务不可修改")

    update_data = data.model_dump(exclude_none=True, exclude={"waypoints"})
    for key, val in update_data.items():
        setattr(task, key, val)

    if data.waypoints is not None:
        await db.execute(delete(TaskWaypoint).where(TaskWaypoint.task_id == task_id))
        for wp in data.waypoints:
            waypoint = TaskWaypoint(
                task_id=task_id,
                seq=wp.seq,
                longitude=wp.longitude,
                latitude=wp.latitude,
                altitude=wp.altitude,
            )
            db.add(waypoint)

    await db.flush()
    return task


async def update_status(db: AsyncSession, task_id: str, tenant_id: str, status: str) -> Task:
    task = await get_by_id(db, task_id, tenant_id)
    valid_transitions = {
        "pending": ["in_progress", "cancelled"],
        "in_progress": ["completed", "cancelled"],
    }
    if status not in valid_transitions.get(task.status, []):
        raise ParamException(f"状态 [{task.status}] 不可转换为 [{status}]")

    task.status = status
    if status == "in_progress":
        task.started_at = datetime.utcnow()
        await db.execute(
            update(Drone).where(Drone.id == task.drone_id).values(
                status="in_task", current_task_id=task_id
            )
        )
    elif status in ("completed", "cancelled"):
        task.completed_at = datetime.utcnow()
        await db.execute(
            update(Drone).where(Drone.id == task.drone_id).values(
                status="online", current_task_id=None
            )
        )

    await db.flush()
    return task


async def delete_task(db: AsyncSession, task_id: str, tenant_id: str):
    task = await get_by_id(db, task_id, tenant_id)
    if task.status == "in_progress":
        raise ParamException("进行中的任务不可删除")
    await db.execute(delete(TaskWaypoint).where(TaskWaypoint.task_id == task_id))
    await db.delete(task)
    await db.flush()
