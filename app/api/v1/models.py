from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, require_roles, get_current_user
from app.schemas.common import ResponseModel, PageData
from app.schemas.model import AIModelOut, ModelCompareJobCreate, ModelCompareJobOut
from app.models.ai_model import AIModel
from app.models.model_compare import ModelCompareJob
from app.models.user import User
import uuid
from datetime import datetime

router = APIRouter(prefix="/models", tags=["AI模型管理"])


@router.get("", response_model=ResponseModel[PageData[AIModelOut]], summary="模型列表")
async def list_models(
    scene: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[权限] 所有登录用户"""
    stmt = select(AIModel)
    if scene:
        stmt = stmt.where(AIModel.scene == scene)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size).order_by(AIModel.published_at.desc())
    rows = (await db.execute(stmt)).scalars().all()

    return ResponseModel.ok(data=PageData(
        total=total, page=page, size=size,
        list=[AIModelOut.model_validate(r) for r in rows]
    ))


@router.get("/{model_id}", response_model=ResponseModel[AIModelOut], summary="模型详情")
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[权限] 所有登录用户"""
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("模型不存在")
    return ResponseModel.ok(data=AIModelOut.model_validate(model))


@router.post("/compare", response_model=ResponseModel[ModelCompareJobOut], summary="提交模型对比任务")
async def create_compare(
    body: ModelCompareJobCreate,
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst"""
    job_id = f"cmp_{uuid.uuid4().hex[:10]}"
    job = ModelCompareJob(
        id=job_id,
        tenant_id=current_user.tenant_id,
        model_a_id=body.model_a_id,
        model_b_id=body.model_b_id,
        video_url=body.video_url,
        status="pending",
        created_by=current_user.id,
    )
    db.add(job)
    await db.flush()
    return ResponseModel.ok(data=ModelCompareJobOut.model_validate(job), message="对比任务已提交")


@router.get("/compare/jobs", response_model=ResponseModel, summary="我的对比任务列表")
async def list_compare_jobs(
    current_user: User = Depends(require_roles("enterprise_admin", "analyst")),
    db: AsyncSession = Depends(get_db),
):
    """[权限] enterprise_admin / analyst"""
    result = await db.execute(
        select(ModelCompareJob)
        .where(ModelCompareJob.tenant_id == current_user.tenant_id)
        .order_by(ModelCompareJob.created_at.desc())
        .limit(20)
    )
    jobs = result.scalars().all()
    return ResponseModel.ok(data=[ModelCompareJobOut.model_validate(j) for j in jobs])
