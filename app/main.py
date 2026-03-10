import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import settings
from app.api.v1.router import api_router
from app.core.exceptions import BusinessException
from app.core.middleware import LoggingMiddleware
from app.db.redis import close_redis

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("drone.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 无人机SaaS平台后端服务启动")
    yield
    await close_redis()
    logger.info("服务已停止")


app = FastAPI(
    title="无人机SaaS平台 API",
    description="小目标检测无人机 SaaS 平台后端接口文档",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.biz_code, "message": exc.message, "data": None},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 40001, "message": f"参数验证失败: {exc.errors()[0]['msg']}", "data": None},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("未捕获异常", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"code": 50001, "message": "服务器内部错误", "data": None},
    )


@app.get("/health", tags=["健康检查"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
