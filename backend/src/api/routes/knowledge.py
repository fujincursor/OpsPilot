"""知识库管理 API"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Body

from ...models.knowledge import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    Document,
    DocumentCreate,
    DocumentResponse,
    KnowledgeReadyStatus,
    KnowledgeSearchQuery,
    KnowledgeSearchResponse,
)
from ...services.knowledge_service import knowledge_service

router = APIRouter()


@router.get(
    "/projects/{project_id}/knowledge",
    response_model=KnowledgeBaseResponse,
    summary="获取知识库列表"
)
async def list_knowledge_bases(project_id: UUID) -> KnowledgeBaseResponse:
    """
    获取项目的知识库列表

    - **project_id**: 项目 ID
    """
    items = knowledge_service.get_knowledge_bases(project_id)
    return KnowledgeBaseResponse(items=items, total=len(items))


@router.post(
    "/projects/{project_id}/knowledge",
    response_model=KnowledgeBase,
    status_code=201,
    summary="创建知识库"
)
async def create_knowledge_base(
    project_id: UUID,
    data: KnowledgeBaseCreate
) -> KnowledgeBase:
    """
    创建新知识库

    - **project_id**: 项目 ID
    - **name**: 知识库名称 (必填, 1-100字符)
    - **description**: 知识库描述 (可选, 最多500字符)
    - **type**: 知识库类型 (doc/code/faq)
    """
    return knowledge_service.create_knowledge_base(project_id, data)


@router.get(
    "/knowledge/{kb_id}",
    response_model=KnowledgeBase,
    summary="获取知识库详情"
)
async def get_knowledge_base(kb_id: UUID) -> KnowledgeBase:
    """
    获取单个知识库详情

    - **kb_id**: 知识库 ID
    """
    kb = knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.put(
    "/knowledge/{kb_id}",
    response_model=KnowledgeBase,
    summary="更新知识库"
)
async def update_knowledge_base(
    kb_id: UUID,
    data: KnowledgeBaseUpdate
) -> KnowledgeBase:
    """
    更新知识库信息

    - **kb_id**: 知识库 ID
    """
    kb = knowledge_service.update_knowledge_base(kb_id, data)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.post(
    "/knowledge/{kb_id}/index",
    response_model=KnowledgeBase,
    summary="触发索引",
)
async def start_knowledge_index(kb_id: UUID) -> KnowledgeBase:
    """按知识库上的范围和策略记录一次索引任务。"""
    kb = knowledge_service.start_index(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete(
    "/knowledge/{kb_id}",
    status_code=204,
    summary="删除知识库"
)
async def delete_knowledge_base(kb_id: UUID):
    """
    删除知识库及其所有文档

    - **kb_id**: 知识库 ID
    """
    if not knowledge_service.delete_knowledge_base(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.get(
    "/knowledge/{kb_id}/documents",
    response_model=DocumentResponse,
    summary="获取文档列表"
)
async def list_documents(kb_id: UUID) -> DocumentResponse:
    """
    获取知识库的文档列表

    - **kb_id**: 知识库 ID
    """
    kb = knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    items = knowledge_service.get_documents(kb_id)
    return DocumentResponse(items=items, total=len(items))


@router.post(
    "/knowledge/{kb_id}/documents",
    response_model=Document,
    status_code=201,
    summary="上传文档"
)
async def add_document(
    kb_id: UUID,
    data: DocumentCreate
) -> Document:
    """
    向知识库添加文档

    - **kb_id**: 知识库 ID
    - **title**: 文档标题 (必填)
    - **content**: 文档内容 (可选)
    - **file_path**: 文件路径 (可选)
    - **file_type**: 文件类型 (可选)
    """
    doc = knowledge_service.add_document(kb_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return doc


@router.delete(
    "/documents/{doc_id}",
    status_code=204,
    summary="删除文档"
)
async def delete_document(doc_id: UUID):
    """
    删除文档

    - **doc_id**: 文档 ID
    """
    if not knowledge_service.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")


@router.post(
    "/projects/{project_id}/knowledge/search",
    response_model=KnowledgeSearchResponse,
    summary="知识检索"
)
async def search_knowledge(
    project_id: UUID,
    query: KnowledgeSearchQuery
) -> KnowledgeSearchResponse:
    """
    在项目知识库中进行语义检索

    - **project_id**: 项目 ID
    - **query**: 检索查询文本
    - **top_k**: 返回结果数量 (默认5, 最大20)
    - **knowledge_base_ids**: 指定知识库 ID 列表 (可选)
    """
    results = knowledge_service.search_knowledge(
        project_id=project_id,
        query=query.query,
        top_k=query.top_k,
        knowledge_base_ids=query.knowledge_base_ids
    )
    return KnowledgeSearchResponse(
        query=query.query,
        results=results,
        total=len(results)
    )


@router.get(
    "/projects/{project_id}/knowledge/status",
    response_model=KnowledgeReadyStatus,
    summary="知识就绪状态"
)
async def get_knowledge_status(project_id: UUID) -> KnowledgeReadyStatus:
    """
    检查项目知识库就绪状态

    返回知识库整体就绪状态，用于判断是否可以进入需求处理流程

    - **project_id**: 项目 ID
    """
    return knowledge_service.check_knowledge_ready(project_id)
