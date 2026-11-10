"""知识就绪校验中间件"""

from typing import Callable, List, Optional
from uuid import UUID

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from ...services.knowledge_service import knowledge_service


class KnowledgeCheckMiddleware(BaseHTTPMiddleware):
    """知识就绪校验中间件

    在进入需求处理流程前校验项目知识库是否就绪
    """

    PROTECTED_PATH_PREFIXES: List[str] = [
        "/api/v1/requirements",
        "/api/v1/chat",
        "/api/v1/analysis",
    ]

    EXCLUDED_METHODS: List[str] = ["OPTIONS", "HEAD"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._should_check(request):
            return await call_next(request)

        project_id = self._extract_project_id(request)
        if not project_id:
            return await call_next(request)

        try:
            project_uuid = UUID(project_id)
        except ValueError:
            return await call_next(request)

        status = knowledge_service.check_knowledge_ready(project_uuid)
        if not status.is_ready:
            return JSONResponse(
                status_code=428,
                content={
                    "detail": "Knowledge base not ready",
                    "message": status.message,
                    "status": {
                        "project_id": str(status.project_id),
                        "is_ready": status.is_ready,
                        "total_knowledge_bases": status.total_knowledge_bases,
                        "ready_knowledge_bases": status.ready_knowledge_bases,
                    }
                }
            )

        return await call_next(request)

    def _should_check(self, request: Request) -> bool:
        """判断是否需要进行知识就绪校验"""
        if request.method in self.EXCLUDED_METHODS:
            return False

        path = request.url.path
        return any(path.startswith(prefix) for prefix in self.PROTECTED_PATH_PREFIXES)

    def _extract_project_id(self, request: Request) -> Optional[str]:
        """从请求中提取项目 ID

        优先级:
        1. Header: X-Project-ID
        2. Path parameter
        3. Query parameter
        """
        if "X-Project-ID" in request.headers:
            return request.headers["X-Project-ID"]

        path_parts = request.url.path.split("/")
        if "projects" in path_parts:
            idx = path_parts.index("projects")
            if idx + 1 < len(path_parts) and path_parts[idx + 1]:
                candidate = path_parts[idx + 1]
                if not candidate.startswith("{"):
                    return candidate

        if "project_id" in request.query_params:
            return request.query_params["project_id"]

        return getattr(request.state, "project_id", None)


def require_knowledge_ready(project_id: UUID) -> None:
    """依赖注入函数：要求知识库就绪

    在需要知识库就绪的路由中使用:

    ```python
    from fastapi import Depends

    @router.post("/projects/{project_id}/requirements")
    async def create_requirement(
        project_id: UUID,
        _: None = Depends(lambda: require_knowledge_ready(project_id))
    ):
        ...
    ```

    如果知识库未就绪，抛出 428 Precondition Required 异常
    """
    status = knowledge_service.check_knowledge_ready(project_id)
    if not status.is_ready:
        raise HTTPException(
            status_code=428,
            detail={
                "message": "Knowledge base not ready",
                "status": status.message,
                "total_knowledge_bases": status.total_knowledge_bases,
                "ready_knowledge_bases": status.ready_knowledge_bases,
            }
        )


async def get_knowledge_ready_dependency(request: Request) -> bool:
    """FastAPI 依赖：检查知识库是否就绪

    使用方式:
    ```python
    from fastapi import Depends

    @router.post("/projects/{project_id}/requirements")
    async def create_requirement(
        project_id: UUID,
        kb_ready: bool = Depends(get_knowledge_ready_dependency)
    ):
        if not kb_ready:
            raise HTTPException(status_code=428, detail="Knowledge not ready")
        ...
    ```
    """
    project_id = getattr(request.state, "project_id", None)
    if not project_id:
        return False

    try:
        project_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
        status = knowledge_service.check_knowledge_ready(project_uuid)
        return status.is_ready
    except (ValueError, TypeError):
        return False
