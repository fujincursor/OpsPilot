"""HITL Review 模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReviewItemType(str, Enum):
    """审核项类型"""
    SOLUTION = "solution"
    CODE = "code"
    TEST = "test"


class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ReviewPriority(str, Enum):
    """审核优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ReviewDecisionType(str, Enum):
    """审核决定类型"""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"


class ReviewCommentBase(BaseModel):
    """审核评论基础模型"""
    content: str = Field(..., min_length=1, max_length=5000, description="评论内容")


class ReviewCommentCreate(ReviewCommentBase):
    """创建评论请求模型"""
    pass


class ReviewComment(ReviewCommentBase):
    """审核评论模型"""
    id: UUID = Field(default_factory=uuid4, description="评论 ID")
    review_item_id: UUID = Field(..., description="关联审核项 ID")
    author: str = Field(..., description="评论作者")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class ReviewDecision(BaseModel):
    """审核决定模型"""
    id: UUID = Field(default_factory=uuid4, description="决定 ID")
    review_item_id: UUID = Field(..., description="关联审核项 ID")
    decision: ReviewDecisionType = Field(..., description="审核决定")
    reviewer: str = Field(..., description="审核人")
    reason: str = Field(default="", description="决定理由")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class ReviewItemBase(BaseModel):
    """审核项基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    description: str = Field(default="", max_length=5000, description="描述")


class ReviewItemCreate(ReviewItemBase):
    """创建审核项请求模型"""
    item_type: ReviewItemType = Field(..., description="审核项类型")
    item_id: UUID = Field(..., description="关联对象 ID")
    project_id: UUID = Field(..., description="项目 ID")
    priority: ReviewPriority = Field(default=ReviewPriority.MEDIUM, description="优先级")
    due_at: Optional[datetime] = Field(None, description="截止时间")


class ReviewItemUpdate(BaseModel):
    """更新审核项请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    description: Optional[str] = Field(None, max_length=5000, description="描述")
    priority: Optional[ReviewPriority] = Field(None, description="优先级")
    reviewer: Optional[str] = Field(None, description="审核人")
    due_at: Optional[datetime] = Field(None, description="截止时间")


class ReviewItem(ReviewItemBase):
    """审核项完整模型"""
    id: UUID = Field(default_factory=uuid4, description="审核项 ID")
    item_type: ReviewItemType = Field(..., description="审核项类型")
    item_id: UUID = Field(..., description="关联对象 ID")
    project_id: UUID = Field(..., description="项目 ID")
    status: ReviewStatus = Field(default=ReviewStatus.PENDING, description="审核状态")
    priority: ReviewPriority = Field(default=ReviewPriority.MEDIUM, description="优先级")
    reviewer: Optional[str] = Field(None, description="审核人")
    comments: List[ReviewComment] = Field(default_factory=list, description="评论列表")
    decisions: List[ReviewDecision] = Field(default_factory=list, description="决定历史")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    due_at: Optional[datetime] = Field(None, description="截止时间")

    class Config:
        from_attributes = True


class ReviewApproveRequest(BaseModel):
    """通过审核请求模型"""
    reason: str = Field(default="", max_length=2000, description="通过理由")


class ReviewRejectRequest(BaseModel):
    """拒绝审核请求模型"""
    reason: str = Field(..., min_length=1, max_length=2000, description="拒绝理由")


class ReviewRevisionRequest(BaseModel):
    """要求修改请求模型"""
    comments: str = Field(..., min_length=1, max_length=5000, description="修改意见")


class ReviewItemResponse(BaseModel):
    """审核项列表响应模型"""
    items: List[ReviewItem]
    total: int
    page: int = 1
    page_size: int = 20


class ReviewCommentResponse(BaseModel):
    """评论列表响应模型"""
    items: List[ReviewComment]
    total: int


class ReviewHistoryEntry(BaseModel):
    """审核历史条目"""
    id: UUID = Field(..., description="条目 ID")
    action: str = Field(..., description="操作类型")
    actor: str = Field(..., description="操作人")
    details: str = Field(default="", description="详情")
    created_at: datetime = Field(..., description="操作时间")


class ReviewHistoryResponse(BaseModel):
    """审核历史响应模型"""
    items: List[ReviewHistoryEntry]
    total: int


class ReviewFilters(BaseModel):
    """审核项过滤条件"""
    item_type: Optional[ReviewItemType] = None
    status: Optional[ReviewStatus] = None
    priority: Optional[ReviewPriority] = None
    reviewer: Optional[str] = None


class NotificationType(str, Enum):
    """通知类型"""
    REVIEW_CREATED = "review_created"
    REVIEW_ASSIGNED = "review_assigned"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    REVIEW_REVISION_REQUESTED = "review_revision_requested"
    REVIEW_COMMENTED = "review_commented"
    REVIEW_TIMEOUT_WARNING = "review_timeout_warning"


class Notification(BaseModel):
    """通知模型"""
    id: UUID = Field(default_factory=uuid4, description="通知 ID")
    user_id: str = Field(..., description="接收用户 ID")
    type: NotificationType = Field(..., description="通知类型")
    title: str = Field(..., description="通知标题")
    content: str = Field(default="", description="通知内容")
    review_item_id: Optional[UUID] = Field(None, description="关联审核项 ID")
    is_read: bool = Field(default=False, description="是否已读")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """通知列表响应模型"""
    items: List[Notification]
    total: int
    unread_count: int
