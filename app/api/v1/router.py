from fastapi import APIRouter
from app.api.v1 import auth, drones, tasks, alerts, reports, dashboard, users, models, plans, quota, platform, monitor

api_router = APIRouter(prefix="/v1")

api_router.include_router(auth.router)
api_router.include_router(drones.router)
api_router.include_router(tasks.router)
api_router.include_router(alerts.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
api_router.include_router(models.router)
api_router.include_router(plans.router)
api_router.include_router(quota.router)
api_router.include_router(platform.router)
api_router.include_router(monitor.router)
