import time
import logging
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("drone.api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - 开始处理"
        )

        response: Response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- 完成 {response.status_code} ({process_time:.1f}ms)"
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.1f}ms"
        return response
