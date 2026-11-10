"""对话会话模型。"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChatKnowledgeHit(BaseModel):
    """回复引用的知识片段。"""
    title: str
    snippet: str
    score: float = 0
    knowledge_base_name: str = ""
    document_id: Optional[str] = None


class ChatClassification(BaseModel):
    """语义分类结果。"""
    type: str
    priority: str
    title: str = ""
    ticket_id: Optional[str] = None


class ChatReviewCard(BaseModel):
    """对话流中的审批卡片。"""
    review_id: str
    item_type: str
    title: str
    status: str
    summary: str
    root_cause: str = ""
    files: List[str] = Field(default_factory=list)
    due_at: Optional[str] = None


class ChatMessage(BaseModel):
    """一条对话消息。"""
    id: UUID = Field(default_factory=uuid4)
    role: str = Field(..., description="user 或 agent")
    content: str
    sender: str
    status: Optional[str] = None
    knowledge_results: List[ChatKnowledgeHit] = Field(default_factory=list)
    classification: Optional[ChatClassification] = None
    review: Optional[ChatReviewCard] = None
    knowledge_blocked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    """一个项目下的对话会话。"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    title: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSessionSummary(BaseModel):
    """会话列表项。"""
    id: UUID
    project_id: UUID
    title: str
    message_count: int
    status: str
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    items: List[ChatSessionSummary]
    total: int
