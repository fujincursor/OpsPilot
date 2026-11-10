"""认证相关模型"""

from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token 响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class TokenPayload(BaseModel):
    """Token 载荷模型"""
    sub: str = Field(..., description="用户ID")
    exp: int = Field(..., description="过期时间戳")
    iat: int = Field(..., description="签发时间戳")
    type: str = Field(default="access", description="令牌类型: access/refresh")


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenData(BaseModel):
    """从 Token 解析出的数据"""
    user_id: Optional[str] = None
    token_type: Optional[str] = None
