"""需求工单模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    """需求类型"""
    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"


class RequirementStatus(str, Enum):
    """需求状态"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    REVIEWING = "reviewing"
    CODING = "coding"
    TESTING = "testing"
    COMPLETED = "completed"
    CLOSED = "closed"


class RequirementPriority(str, Enum):
    """需求优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementSource(str, Enum):
    """需求来源"""
    WEB = "web"
    IM = "im"
    API = "api"


class RequirementBase(BaseModel):
    """需求基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="需求标题")
    description: str = Field(..., min_length=1, max_length=5000, description="需求描述")
    source: RequirementSource = Field(default=RequirementSource.WEB, description="需求来源")


class RequirementCreate(RequirementBase):
    """创建需求请求模型"""
    type: Optional[RequirementType] = Field(None, description="需求类型（可选，不填则自动分析）")
    priority: Optional[RequirementPriority] = Field(None, description="优先级（可选，不填则自动分析）")


class RequirementUpdate(BaseModel):
    """更新需求请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="需求标题")
    description: Optional[str] = Field(None, min_length=1, max_length=5000, description="需求描述")
    type: Optional[RequirementType] = Field(None, description="需求类型")
    priority: Optional[RequirementPriority] = Field(None, description="优先级")


class RequirementStatusUpdate(BaseModel):
    """更新需求状态请求模型"""
    status: RequirementStatus = Field(..., description="新状态")


class RequirementAssignUpdate(BaseModel):
    """分配需求请求模型"""
    assignee: str = Field(..., min_length=1, max_length=100, description="分配人")


class RequirementAnalysis(BaseModel):
    """需求分析结果"""
    type: RequirementType = Field(..., description="识别的需求类型")
    priority: RequirementPriority = Field(..., description="建议的优先级")
    keywords: List[str] = Field(default_factory=list, description="提取的关键词")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="分析置信度")


class RequirementAnalyzeRequest(BaseModel):
    """需求分析请求模型"""
    text: str = Field(..., min_length=1, max_length=5000, description="需求文本")


class Requirement(RequirementBase):
    """需求完整模型"""
    id: UUID = Field(default_factory=uuid4, description="需求 ID")
    project_id: UUID = Field(..., description="所属项目 ID")
    type: RequirementType = Field(default=RequirementType.FEATURE, description="需求类型")
    priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="优先级")
    status: RequirementStatus = Field(default=RequirementStatus.PENDING, description="需求状态")
    assignee: Optional[str] = Field(None, description="分配人")
    created_by: Optional[str] = Field(None, description="创建人")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    analysis_confidence: float = Field(default=0.0, description="AI 分析置信度")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        from_attributes = True


class RequirementResponse(BaseModel):
    """需求列表响应模型"""
    items: List[Requirement]
    total: int
    page: int = 1
    page_size: int = 20


class RequirementFilters(BaseModel):
    """需求过滤条件"""
    type: Optional[RequirementType] = None
    status: Optional[RequirementStatus] = None
    priority: Optional[RequirementPriority] = None
    assignee: Optional[str] = None
    keyword: Optional[str] = None
