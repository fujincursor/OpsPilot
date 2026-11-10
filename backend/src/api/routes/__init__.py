"""路由模块"""

from fastapi import APIRouter

from .health import router as health_router
from .projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
