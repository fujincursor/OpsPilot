"""对话会话接口。"""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...models.chat import ChatSession, ChatSessionListResponse
from ...services.chat_service import chat_service

router = APIRouter(tags=["chat"])


@router.get("/projects/{project_id}/chats", response_model=ChatSessionListResponse)
async def list_chats(project_id: UUID) -> ChatSessionListResponse:
    """列出项目下已保存的对话。"""
    items = chat_service.list_sessions(project_id)
    return ChatSessionListResponse(items=items, total=len(items))


@router.get("/chats/{session_id}", response_model=ChatSession)
async def get_chat(session_id: UUID) -> ChatSession:
    """读取一个对话的全部消息。"""
    session = chat_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="对话不存在")
    return session
