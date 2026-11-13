"""FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import flush_dirty
from .api.routes import api_router
from .api.routes.health import router as health_router
from .api.middleware import JWTAuthMiddleware, ProjectContextMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="OpsPilot 运维领航 - 智能运维助手后端服务",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(ProjectContextMiddleware)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

@app.middleware("http")
async def persist_request_changes(request, call_next):
    """写操作结束后把内存中的修改同步到数据库。登录只签发令牌，不重写全部集合。"""
    response = await call_next(request)
    path = request.url.path
    skip_flush = path in {
        f"{settings.api_v1_prefix}/auth/login",
        f"{settings.api_v1_prefix}/auth/refresh",
    }
    if request.method not in {"GET", "HEAD", "OPTIONS"} and not skip_flush:
        flush_dirty()
    return response


app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
