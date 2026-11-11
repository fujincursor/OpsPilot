"""路由模块"""

from fastapi import APIRouter

from .auth import router as auth_router
from .health import router as health_router
from .projects import router as projects_router
from .agents import router as agents_router
from .knowledge import router as knowledge_router
from .requirements import router as requirements_router
from .solutions import router as solutions_router
from .reviews import router as reviews_router
from .codegen import router as codegen_router
from .tests import router as tests_router
from .analytics import router as analytics_router
from .deerflow import router as deerflow_router
from .chat import router as chat_router
from .workflow import router as workflow_router
from .skills import router as skills_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(requirements_router, tags=["requirements"])
api_router.include_router(solutions_router, tags=["solutions"])
api_router.include_router(reviews_router, tags=["reviews"])
api_router.include_router(codegen_router, tags=["codegen"])
api_router.include_router(tests_router, tags=["tests"])
api_router.include_router(analytics_router, tags=["analytics"])
api_router.include_router(deerflow_router)
api_router.include_router(chat_router)
api_router.include_router(workflow_router, tags=["workflow"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
