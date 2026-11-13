"""知识库服务"""

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from ..db import DocumentDict
from ..models.knowledge import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeStatus,
    Document,
    DocumentCreate,
    EmbeddingStatus,
    KnowledgeReadyStatus,
    KnowledgeSearchResult,
    IndexJob,
)
from .knowledge_indexer import chunk_text, embed_texts, parse_document
from .vector_store import VectorStoreUnavailable, delete_document, search as search_chunks, upsert_chunks

if TYPE_CHECKING:
    from .project_service import ProjectService


class KnowledgeService:
    """知识库管理服务

    文档上传后会解析、分块、向量化，并按向量相似度检索。
    """

    def __init__(self):
        self._knowledge_bases: Dict[UUID, KnowledgeBase] = DocumentDict(
            "knowledge_bases",
            model=KnowledgeBase,
        )
        self._documents: Dict[UUID, Document] = DocumentDict("documents", model=Document)
        self._kb_to_docs: Dict[UUID, List[UUID]] = {}
        for document in self._documents.values():
            self._kb_to_docs.setdefault(document.knowledge_base_id, []).append(document.id)
        self._index_pending_documents()
        self._project_service: Optional["ProjectService"] = None

    def set_project_service(self, project_service: "ProjectService"):
        """设置项目服务引用"""
        self._project_service = project_service

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
        self._knowledge_bases[kb.id] = kb
        return kb

    def start_index(self, kb_id: UUID) -> Optional[KnowledgeBase]:
        """按当前范围记录一次索引任务。"""
        kb = self._knowledge_bases.get(kb_id)
        if not kb:
            return None
        paths = kb.index_paths or ["未设置"]
        job = IndexJob(
            id=uuid4().hex[:8],
            status="completed",
            message=f"已按{kb.update_policy}策略索引：{', '.join(paths)}",
        )
        kb.index_jobs = [job, *list(kb.index_jobs)][:20]
        if kb.status != KnowledgeStatus.ERROR:
            kb.status = KnowledgeStatus.READY
        kb.updated_at = datetime.utcnow()
        self._knowledge_bases[kb.id] = kb
        return kb

    def delete_knowledge_base(self, kb_id: UUID) -> bool:
        """删除知识库及其所有文档"""
        if kb_id not in self._knowledge_bases:
            return False

        doc_ids = list(self._kb_to_docs.get(kb_id, []))
        for doc_id in doc_ids:
            self._delete_chunks(doc_id)
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
            embedding_status=EmbeddingStatus.PROCESSING,
            **data.model_dump()
        )
        self._documents[doc.id] = doc

        if kb_id not in self._kb_to_docs:
            self._kb_to_docs[kb_id] = []
        self._kb_to_docs[kb_id].append(doc.id)
        kb.document_count = len(self._kb_to_docs[kb_id])
        kb.status = KnowledgeStatus.INDEXING
        kb.updated_at = datetime.utcnow()
        self._knowledge_bases[kb.id] = kb

        self._index_document(doc)
        self._refresh_kb_status(kb_id)
        return self._documents[doc.id]

    def delete_document(self, doc_id: UUID) -> bool:
        """删除文档"""
        doc = self._documents.get(doc_id)
        if not doc:
            return False

        kb_id = doc.knowledge_base_id
        self._delete_chunks(doc_id)
        if kb_id in self._kb_to_docs:
            self._kb_to_docs[kb_id] = [
                d_id for d_id in self._kb_to_docs[kb_id] if d_id != doc_id
            ]
            kb = self._knowledge_bases.get(kb_id)
            if kb:
                kb.document_count = len(self._kb_to_docs[kb_id])
                kb.updated_at = datetime.utcnow()
                self._knowledge_bases[kb.id] = kb

        del self._documents[doc_id]
        self._refresh_kb_status(kb_id)
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
        knowledge_base_ids: Optional[List[UUID]] = None,
        snippet_chars: int = 200,
    ) -> List[KnowledgeSearchResult]:
        """按向量相似度检索已完成索引的文档分块。"""
        allowed_ids = {kb.id for kb in self.get_knowledge_bases(project_id)}
        if knowledge_base_ids:
            allowed_ids &= set(knowledge_base_ids)
        if not allowed_ids:
            return []

        model_name, vectors = embed_texts([query])
        query_vector = vectors[0]
        hits = search_chunks(
            query_vector,
            [str(item) for item in allowed_ids],
            model_name,
            max(top_k * 5, top_k),
        )
        best_by_document: dict[UUID, KnowledgeSearchResult] = {}
        for hit in hits:
            payload = hit["payload"]
            document_id = UUID(str(payload.get("document_id")))
            knowledge_base_id = UUID(str(payload.get("knowledge_base_id")))
            document = self._documents.get(document_id)
            if not document or document.embedding_status != EmbeddingStatus.COMPLETED:
                continue
            score = float(hit["score"])
            if score <= 0:
                continue
            current = best_by_document.get(document_id)
            if current and current.score >= score:
                continue
            content = str(payload.get("content") or "")
            snippet = content if len(content) <= snippet_chars else content[:snippet_chars] + "..."
            best_by_document[document_id] = KnowledgeSearchResult(
                document_id=document_id,
                knowledge_base_id=knowledge_base_id,
                title=document.title,
                content_snippet=snippet,
                score=round(score, 4),
            )

        results = sorted(best_by_document.values(), key=lambda item: item.score, reverse=True)
        return results[:top_k]

    def _index_pending_documents(self) -> None:
        """启动时补齐尚未完成向量化的文档。"""
        pending_ids = [
            document.knowledge_base_id
            for document in self._documents.values()
            if document.embedding_status in {EmbeddingStatus.PENDING, EmbeddingStatus.PROCESSING}
        ]
        for document in list(self._documents.values()):
            if document.embedding_status in {EmbeddingStatus.PENDING, EmbeddingStatus.PROCESSING}:
                try:
                    self._index_document(document)
                except VectorStoreUnavailable as exc:
                    document.embedding_status = EmbeddingStatus.FAILED
                    document.error_message = str(exc)
                    document.chunk_count = 0
                    self._documents[document.id] = document
        for kb_id in set(pending_ids):
            self._refresh_kb_status(kb_id)

    def _index_document(self, document: Document) -> None:
        """解析文档、切分并写入向量。"""
        try:
            text = parse_document(document.content, document.file_type)
            pieces = chunk_text(text)
            model_name, vectors = embed_texts(pieces)
        except Exception as exc:
            document.embedding_status = EmbeddingStatus.FAILED
            document.error_message = str(exc)
            document.chunk_count = 0
            self._documents[document.id] = document
            return

        self._delete_chunks(document.id)
        knowledge_base = self._knowledge_bases.get(document.knowledge_base_id)
        project_id = str(knowledge_base.project_id) if knowledge_base else ""
        upsert_chunks([
            {
                "id": uuid4(),
                "vector": vector,
                "payload": {
                    "document_id": str(document.id),
                    "knowledge_base_id": str(document.knowledge_base_id),
                    "project_id": project_id,
                    "content": piece,
                    "chunk_index": index,
                    "embedding_model": model_name,
                },
            }
            for index, (piece, vector) in enumerate(zip(pieces, vectors))
        ])

        document.embedding_status = EmbeddingStatus.COMPLETED
        document.embedding_model = model_name
        document.chunk_count = len(pieces)
        document.error_message = None
        self._documents[document.id] = document

    def _delete_chunks(self, document_id: UUID) -> None:
        delete_document(document_id)

    def _refresh_kb_status(self, kb_id: UUID) -> None:
        kb = self._knowledge_bases.get(kb_id)
        if not kb:
            return
        documents = self.get_documents(kb_id)
        if not documents:
            kb.status = KnowledgeStatus.PENDING
        elif any(item.embedding_status == EmbeddingStatus.PROCESSING for item in documents):
            kb.status = KnowledgeStatus.INDEXING
        elif all(item.embedding_status == EmbeddingStatus.FAILED for item in documents):
            kb.status = KnowledgeStatus.ERROR
        elif all(item.embedding_status == EmbeddingStatus.COMPLETED for item in documents):
            kb.status = KnowledgeStatus.READY
        elif any(item.embedding_status == EmbeddingStatus.COMPLETED for item in documents):
            kb.status = KnowledgeStatus.READY
        else:
            kb.status = KnowledgeStatus.PENDING
        kb.updated_at = datetime.utcnow()
        self._knowledge_bases[kb.id] = kb

    def update_knowledge_status(self, kb_id: UUID, status: KnowledgeStatus) -> bool:
        """更新知识库状态"""
        kb = self._knowledge_bases.get(kb_id)
        if not kb:
            return False

        kb.status = status
        kb.updated_at = datetime.utcnow()
        self._knowledge_bases[kb.id] = kb
        return True

    def update_document_embedding_status(
        self, doc_id: UUID, status: EmbeddingStatus
    ) -> bool:
        """更新文档向量化状态"""
        doc = self._documents.get(doc_id)
        if not doc:
            return False

        doc.embedding_status = status
        self._documents[doc.id] = doc
        return True


knowledge_service = KnowledgeService()
