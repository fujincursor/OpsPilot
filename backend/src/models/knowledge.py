"""知识库模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class KnowledgeType(str, Enum):
    """知识库类型"""
    DOC = "doc"
    CODE = "code"
    FAQ = "faq"


class KnowledgeStatus(str, Enum):
    """知识库状态"""
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class EmbeddingStatus(str, Enum):
    """文档向量化状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_type: Optional[str] = Field(None, description="文件类型")


class DocumentCreate(DocumentBase):
    """创建文档请求模型"""
    pass


class Document(DocumentBase):
    """文档完整模型"""
    id: UUID = Field(default_factory=uuid4, description="文档 ID")
    knowledge_base_id: UUID = Field(..., description="所属知识库 ID")
    embedding_status: EmbeddingStatus = Field(
        default=EmbeddingStatus.PENDING, description="向量化状态"
    )
    embedding_model: Optional[str] = Field(None, description="向量模型")
    chunk_count: int = Field(default=0, description="分块数量")
    error_message: Optional[str] = Field(None, description="处理失败原因")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class KnowledgeChunk(BaseModel):
    """文档分块及其向量"""
    id: UUID = Field(default_factory=uuid4, description="分块 ID")
    document_id: UUID = Field(..., description="文档 ID")
    knowledge_base_id: UUID = Field(..., description="知识库 ID")
    chunk_index: int = Field(..., ge=0, description="分块序号")
    content: str = Field(..., description="分块文本")
    embedding: List[float] = Field(default_factory=list, description="向量")
    embedding_model: str = Field(..., description="向量模型")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class DocumentResponse(BaseModel):
    """文档列表响应模型"""
    items: List[Document]
    total: int


class KnowledgeBaseBase(BaseModel):
    """知识库基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=500, description="知识库描述")
    type: KnowledgeType = Field(default=KnowledgeType.DOC, description="知识库类型")


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """创建知识库请求模型"""
    pass


class IndexJob(BaseModel):
    """一次代码或文档索引任务。"""
    id: str
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=500, description="知识库描述")
    type: Optional[KnowledgeType] = Field(None, description="知识库类型")
    index_paths: Optional[List[str]] = Field(None, description="索引范围")
    index_trigger: Optional[str] = Field(None, description="触发方式")
    update_policy: Optional[str] = Field(None, description="更新策略")


class KnowledgeBase(KnowledgeBaseBase):
    """知识库完整模型"""
    id: UUID = Field(default_factory=uuid4, description="知识库 ID")
    project_id: UUID = Field(..., description="所属项目 ID")
    status: KnowledgeStatus = Field(default=KnowledgeStatus.PENDING, description="知识库状态")
    document_count: int = Field(default=0, description="文档数量")
    index_paths: List[str] = Field(default_factory=lambda: ["src"], description="索引范围")
    index_trigger: str = Field(default="manual", description="触发方式")
    update_policy: str = Field(default="incremental", description="更新策略")
    index_jobs: List[IndexJob] = Field(default_factory=list, description="索引任务")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        from_attributes = True


class KnowledgeBaseResponse(BaseModel):
    """知识库列表响应模型"""
    items: List[KnowledgeBase]
    total: int


class KnowledgeReadyStatus(BaseModel):
    """知识库就绪状态"""
    project_id: UUID = Field(..., description="项目 ID")
    is_ready: bool = Field(..., description="是否就绪")
    total_knowledge_bases: int = Field(default=0, description="知识库总数")
    ready_knowledge_bases: int = Field(default=0, description="就绪的知识库数量")
    message: str = Field(default="", description="状态消息")


class KnowledgeSearchQuery(BaseModel):
    """知识检索请求模型"""
    query: str = Field(..., min_length=1, max_length=1000, description="检索查询")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    knowledge_base_ids: Optional[List[UUID]] = Field(None, description="指定知识库 ID 列表")


class KnowledgeSearchResult(BaseModel):
    """知识检索结果"""
    document_id: UUID = Field(..., description="文档 ID")
    knowledge_base_id: UUID = Field(..., description="知识库 ID")
    title: str = Field(..., description="文档标题")
    content_snippet: str = Field(..., description="内容片段")
    score: float = Field(..., description="相似度分数")


class KnowledgeSearchResponse(BaseModel):
    """知识检索响应"""
    query: str = Field(..., description="原始查询")
    results: List[KnowledgeSearchResult] = Field(default_factory=list, description="检索结果")
    total: int = Field(default=0, description="结果总数")
