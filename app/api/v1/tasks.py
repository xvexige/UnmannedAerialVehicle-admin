from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles, pagination
from app.schemas.common import ResponseModel, PageData
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskDetail, TaskListItem
from app.services import task_service
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["任务管理"])


@router.get("", response_model=ResponseModel[PageData[TaskListItem]], summary="获取任务列表")
async def list_tasks(
    status: str | None = Query(None),
    assignee_id: str | None = Query(None),
    pager: dict = Depends(pagination),
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    actual_assignee = assignee_id
    if current_user.role == "pilot":
        actual_assignee = current_user.id
    result = await task_service.get_list(
        db, current_user.tenant_id, pager["page"], pager["size"], status, actual_assignee
    )
    return ResponseModel.ok(data=result)


@router.get("/{task_id}", response_model=ResponseModel[TaskDetail], summary="获取任务详情")
async def get_task(
    task_id: str,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot / analyst"""
    task = await task_service.get_by_id(db, task_id, current_user.tenant_id)
    waypoints = await task_service.get_waypoints(db, task_id)
    detail = TaskDetail.model_validate(task)
    detail.waypoints = [w for w in waypoints]
    return ResponseModel.ok(data=detail)


@router.post("", response_model=ResponseModel[TaskListItem], summary="创建巡检任务")
async def create_task(
    body: TaskCreate,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    task = await task_service.create(db, current_user.tenant_id, current_user.id, body)
    return ResponseModel.ok(data=TaskListItem.model_validate(task), message="任务创建成功")


@router.put("/{task_id}", response_model=ResponseModel[TaskListItem], summary="更新任务")
async def update_task(
    task_id: str,
    body: TaskUpdate,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    task = await task_service.update_task(db, task_id, current_user.tenant_id, body)
    return ResponseModel.ok(data=TaskListItem.model_validate(task))


@router.patch("/{task_id}/status", response_model=ResponseModel[TaskListItem], summary="更新任务状态")
async def update_task_status(
    task_id: str,
    body: TaskStatusUpdate,
    current_user: User = Depends(require_roles("enterprise_admin", "pilot")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / pilot"""
    task = await task_service.update_status(db, task_id, current_user.tenant_id, body.status)
    return ResponseModel.ok(data=TaskListItem.model_validate(task))


@router.delete("/{task_id}", response_model=ResponseModel, summary="删除任务")
async def delete_task(
    task_id: str,
    current_user: User = Depends(require_roles("enterprise_admin")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin"""
    await task_service.delete_task(db, task_id, current_user.tenant_id)
    return ResponseModel.ok(message="任务已删除")
