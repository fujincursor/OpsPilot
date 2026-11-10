"""FastAPI 依赖注入"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..models.user import User, UserResponse, UserRole
from ..services.user_service import UserService
from .middleware.auth import decode_token
from .middleware.project_context import get_project_id_from_request

security = HTTPBearer(auto_error=False)


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """从请求中获取并验证 Token"""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    return payload


async def get_current_user(
    request: Request,
    payload: Optional[dict] = Depends(get_token_payload),
) -> User:
    """获取当前认证用户

    Raises:
        HTTPException: 未认证或 Token 无效时抛出 401 错误
    """
    user_id = getattr(request.state, "user_id", None)

    if not user_id and payload:
        user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserService.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_user_optional(
    request: Request,
    payload: Optional[dict] = Depends(get_token_payload),
) -> Optional[User]:
    """获取当前用户（可选，不强制认证）"""
    try:
        return await get_current_user(request, payload)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """角色权限检查依赖工厂

    Args:
        allowed_roles: 允许访问的角色列表

    Returns:
        依赖函数
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


async def get_current_project_id(request: Request) -> Optional[str]:
    """获取当前项目 ID"""
    return get_project_id_from_request(request)


async def require_project_context(request: Request) -> str:
    """要求项目上下文存在

    Raises:
        HTTPException: 未提供项目上下文时抛出 400 错误
    """
    project_id = get_project_id_from_request(request)
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project context required. Provide X-Project-ID header or project_id query parameter.",
        )
    return project_id


RequireAdmin = Depends(require_role([UserRole.ADMIN]))
RequireOperator = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
RequireViewer = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER]))
