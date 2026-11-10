"""知识库服务"""

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from ..models.knowledge import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeStatus,
    KnowledgeType,
    Document,
    DocumentCreate,
    EmbeddingStatus,
    KnowledgeReadyStatus,
    KnowledgeSearchResult,
)

if TYPE_CHECKING:
    from .project_service import ProjectService


class KnowledgeService:
    """知识库管理服务

    当前使用内存存储，后续可替换为数据库实现
    向量检索部分为模拟实现，后续可集成向量数据库
    """

    def __init__(self):
        self._knowledge_bases: Dict[UUID, KnowledgeBase] = {}
        self._documents: Dict[UUID, Document] = {}
        self._kb_to_docs: Dict[UUID, List[UUID]] = {}
        self._project_service: Optional["ProjectService"] = None
        self._init_demo_data()

    def set_project_service(self, project_service: "ProjectService"):
        """设置项目服务引用"""
        self._project_service = project_service

    def _init_demo_data(self):
        """初始化演示数据（稍后由服务注入后与项目关联）"""
        pass

    def init_demo_knowledge(self, project_id: UUID):
        """为项目初始化演示知识库"""
        existing = self.get_knowledge_bases(project_id)
        if existing:
            return

        demo_kbs = [
            KnowledgeBaseCreate(
                name="运维手册",
                description="运维操作标准流程文档",
                type=KnowledgeType.DOC
            ),
            KnowledgeBaseCreate(
                name="代码规范",
                description="项目代码规范和最佳实践",
                type=KnowledgeType.CODE
            ),
            KnowledgeBaseCreate(
                name="常见问题",
                description="常见运维问题及解决方案",
                type=KnowledgeType.FAQ
            ),
        ]

        for kb_data in demo_kbs:
            kb = self.create_knowledge_base(project_id, kb_data)
            self._add_demo_documents(kb.id, kb.type)
            kb.status = KnowledgeStatus.READY
            kb.updated_at = datetime.utcnow()

    def _add_demo_documents(self, kb_id: UUID, kb_type: KnowledgeType):
        """添加演示文档"""
        demo_docs_map = {
            KnowledgeType.DOC: [
                DocumentCreate(
                    title="服务器运维手册",
                    content="包含服务器日常运维操作流程...",
                    file_type="markdown"
                ),
                DocumentCreate(
                    title="数据库运维指南",
                    content="数据库备份、恢复、性能优化指南...",
                    file_type="markdown"
                ),
            ],
            KnowledgeType.CODE: [
                DocumentCreate(
                    title="Python 编码规范",
                    content="遵循 PEP8 标准的 Python 代码规范...",
                    file_type="markdown"
                ),
            ],
            KnowledgeType.FAQ: [
                DocumentCreate(
                    title="服务器 CPU 过高怎么办",
                    content="1. 使用 top 命令查看进程...\n2. 分析是否有异常进程...",
                    file_type="markdown"
                ),
                DocumentCreate(
                    title="如何处理磁盘空间不足",
                    content="1. 使用 df -h 查看磁盘使用情况...\n2. 清理日志文件...",
                    file_type="markdown"
                ),
            ],
        }

        docs = demo_docs_map.get(kb_type, [])
        for doc_data in docs:
            doc = self.add_document(kb_id, doc_data)
            if doc:
                doc.embedding_status = EmbeddingStatus.COMPLETED

    def get_knowledge_bases(self, project_id: UUID) -> List[KnowledgeBase]:
        """获取项目的知识库列表"""
        return [
            kb for kb in self._knowledge_bases.values()
            if kb.project_id == project_id
        ]

    def get_knowledge_base(self, kb_id: UUID) -> Optional[KnowledgeBase]:
        """获取单个知识库"""
        return self._knowledge_bases.get(kb_id)

    def create_knowledge_base(
        self, project_id: UUID, data: KnowledgeBaseCreate
    ) -> KnowledgeBase:
        """创建知识库"""
        kb = KnowledgeBase(
            project_id=project_id,
            **data.model_dump()
        )
        self._knowledge_bases[kb.id] = kb
        self._kb_to_docs[kb.id] = []
        return kb

    def update_knowledge_base(
        self, kb_id: UUID, data: KnowledgeBaseUpdate
    ) -> Optional[KnowledgeBase]:
        """更新知识库"""
        kb = self._knowledge_bases.get(kb_id)
        if not kb:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kb, field, value)

        kb.updated_at = datetime.utcnow()
        return kb

    def delete_knowledge_base(self, kb_id: UUID) -> bool:
        """删除知识库及其所有文档"""
        if kb_id not in self._knowledge_bases:
            return False

        doc_ids = self._kb_to_docs.get(kb_id, [])
        for doc_id in doc_ids:
            self._documents.pop(doc_id, None)

        self._kb_to_docs.pop(kb_id, None)
        del self._knowledge_bases[kb_id]
        return True

    def get_documents(self, kb_id: UUID) -> List[Document]:
        """获取知识库的文档列表"""
        doc_ids = self._kb_to_docs.get(kb_id, [])
        return [self._documents[doc_id] for doc_id in doc_ids if doc_id in self._documents]

    def get_document(self, doc_id: UUID) -> Optional[Document]:
        """获取单个文档"""
        return self._documents.get(doc_id)

    def add_document(self, kb_id: UUID, data: DocumentCreate) -> Optional[Document]:
        """添加文档到知识库"""
        kb = self._knowledge_bases.get(kb_id)
        if not kb:
            return None

        doc = Document(
            knowledge_base_id=kb_id,
            **data.model_dump()
        )
        self._documents[doc.id] = doc

        if kb_id not in self._kb_to_docs:
            self._kb_to_docs[kb_id] = []
        self._kb_to_docs[kb_id].append(doc.id)

        kb.document_count = len(self._kb_to_docs[kb_id])
        kb.updated_at = datetime.utcnow()

        if kb.status == KnowledgeStatus.READY:
            kb.status = KnowledgeStatus.INDEXING

        return doc

    def delete_document(self, doc_id: UUID) -> bool:
        """删除文档"""
        doc = self._documents.get(doc_id)
        if not doc:
            return False

        kb_id = doc.knowledge_base_id
        if kb_id in self._kb_to_docs:
            self._kb_to_docs[kb_id] = [
                d_id for d_id in self._kb_to_docs[kb_id] if d_id != doc_id
            ]
            kb = self._knowledge_bases.get(kb_id)
            if kb:
                kb.document_count = len(self._kb_to_docs[kb_id])
                kb.updated_at = datetime.utcnow()

        del self._documents[doc_id]
        return True

    def check_knowledge_ready(self, project_id: UUID) -> KnowledgeReadyStatus:
        """检查项目知识库是否就绪"""
        kbs = self.get_knowledge_bases(project_id)
        total = len(kbs)
        ready = sum(1 for kb in kbs if kb.status == KnowledgeStatus.READY)

        if total == 0:
            return KnowledgeReadyStatus(
                project_id=project_id,
                is_ready=False,
                total_knowledge_bases=0,
                ready_knowledge_bases=0,
                message="项目尚未配置知识库"
            )

        is_ready = ready > 0
        if ready == total:
            message = f"所有 {total} 个知识库已就绪"
        elif ready > 0:
            message = f"{ready}/{total} 个知识库已就绪"
        else:
            indexing = sum(1 for kb in kbs if kb.status == KnowledgeStatus.INDEXING)
            if indexing > 0:
                message = f"{indexing} 个知识库正在索引中"
            else:
                message = "知识库尚未就绪"

        return KnowledgeReadyStatus(
            project_id=project_id,
            is_ready=is_ready,
            total_knowledge_bases=total,
            ready_knowledge_bases=ready,
            message=message
        )

    def search_knowledge(
        self,
        project_id: UUID,
        query: str,
        top_k: int = 5,
        knowledge_base_ids: Optional[List[UUID]] = None
    ) -> List[KnowledgeSearchResult]:
        """知识检索（模拟向量检索）

        当前为简单的关键词匹配模拟实现
        后续可集成向量数据库进行语义检索
        """
        kbs = self.get_knowledge_bases(project_id)
        if knowledge_base_ids:
            kbs = [kb for kb in kbs if kb.id in knowledge_base_ids]

        ready_kbs = [kb for kb in kbs if kb.status == KnowledgeStatus.READY]

        results: List[KnowledgeSearchResult] = []
        query_lower = query.lower()

        for kb in ready_kbs:
            docs = self.get_documents(kb.id)
            for doc in docs:
                if doc.embedding_status != EmbeddingStatus.COMPLETED:
                    continue

                score = self._calculate_relevance_score(doc, query_lower)
                if score > 0:
                    content = doc.content or ""
                    snippet = content[:200] + "..." if len(content) > 200 else content

                    results.append(KnowledgeSearchResult(
                        document_id=doc.id,
                        knowledge_base_id=kb.id,
                        title=doc.title,
                        content_snippet=snippet,
                        score=score
                    ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _calculate_relevance_score(self, doc: Document, query_lower: str) -> float:
        """计算文档与查询的相关度分数（简单模拟）"""
        score = 0.0
        query_terms = query_lower.split()

        title_lower = doc.title.lower()
        content_lower = (doc.content or "").lower()

        for term in query_terms:
            if term in title_lower:
                score += 0.5
            if term in content_lower:
                score += 0.3

        if query_lower in title_lower:
            score += 0.8
        if query_lower in content_lower:
            score += 0.4

        return min(score, 1.0)

    def update_knowledge_status(self, kb_id: UUID, status: KnowledgeStatus) -> bool:
        """更新知识库状态"""
        kb = self._knowledge_bases.get(kb_id)
        if not kb:
            return False

        kb.status = status
        kb.updated_at = datetime.utcnow()
        return True

    def update_document_embedding_status(
        self, doc_id: UUID, status: EmbeddingStatus
    ) -> bool:
        """更新文档向量化状态"""
        doc = self._documents.get(doc_id)
        if not doc:
            return False

        doc.embedding_status = status
        return True


knowledge_service = KnowledgeService()
