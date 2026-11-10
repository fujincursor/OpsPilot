"""路由模块"""

from fastapi import APIRouter

from .auth import router as auth_router
from .health import router as health_router
from .projects import router as projects_router
from .agents import router as agents_router
from .knowledge import router as knowledge_router
from .requirements import router as requirements_router
from .solutions import router as solutions_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(requirements_router, tags=["requirements"])
api_router.include_router(solutions_router, tags=["solutions"])
