"""用户模型"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """用户角色枚举。

    operator 对应开发者，viewer 对应只读需求方，reviewer 负责审批。
    """
    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    role: UserRole = Field(default=UserRole.VIEWER, description="用户角色")


class UserCreate(UserBase):
    """创建用户请求模型"""
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=6)


class User(UserBase):
    """用户完整模型（内部使用）"""
    id: str = Field(..., description="用户ID")
    hashed_password: str = Field(..., description="哈希后的密码")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class UserResponse(BaseModel):
    """用户响应模型（对外展示）"""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(User):
    """数据库中的用户模型"""
    pass
