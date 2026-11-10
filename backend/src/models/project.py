"""项目模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """项目状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, max_length=500, description="项目描述")
    repo_url: Optional[str] = Field(None, description="代码仓库地址")


class ProjectCreate(ProjectBase):
    """创建项目请求模型"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, max_length=500, description="项目描述")
    repo_url: Optional[str] = Field(None, description="代码仓库地址")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")


class Project(ProjectBase):
    """项目完整模型"""
    id: UUID = Field(default_factory=uuid4, description="项目 ID")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="项目状态")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """项目列表响应模型"""
    items: List[Project]
    total: int
    page: int = 1
    page_size: int = 20
