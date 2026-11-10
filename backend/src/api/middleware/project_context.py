"""项目上下文中间件"""

from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class ProjectContextMiddleware(BaseHTTPMiddleware):
    """项目上下文中间件 - 从请求中提取项目 ID"""

    HEADER_NAME = "X-Project-ID"
    QUERY_PARAM = "project_id"

    async def dispatch(self, request: Request, call_next):
        project_id = self._extract_project_id(request)
        request.state.project_id = project_id

        response = await call_next(request)
        return response

    def _extract_project_id(self, request: Request) -> Optional[str]:
        """从请求中提取项目 ID

        优先级:
        1. Header: X-Project-ID
        2. Query parameter: project_id
        3. Path parameter: 从 URL 路径中提取 (如 /projects/{project_id}/...)
        """
        if self.HEADER_NAME in request.headers:
            return request.headers[self.HEADER_NAME]

        if self.QUERY_PARAM in request.query_params:
            return request.query_params[self.QUERY_PARAM]

        path_parts = request.url.path.split("/")
        if "projects" in path_parts:
            idx = path_parts.index("projects")
            if idx + 1 < len(path_parts) and path_parts[idx + 1]:
                project_id_candidate = path_parts[idx + 1]
                if not project_id_candidate.startswith("{"):
                    return project_id_candidate

        return None


def get_project_id_from_request(request: Request) -> Optional[str]:
    """从请求状态中获取项目 ID"""
    return getattr(request.state, "project_id", None)
