"""健康检查接口"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter

from ...config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict:
    """
    健康检查接口

    返回服务状态和基本信息
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready")
async def readiness_check() -> Dict:
    """就绪检查接口"""
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check() -> Dict:
    """存活检查接口"""
    return {"status": "alive"}
