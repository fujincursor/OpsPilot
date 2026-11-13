"""对话会话持久化。"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..db import DocumentDict
from ..models.chat import (
    ChatClassification,
    ChatKnowledgeHit,
    ChatMessage,
    ChatReviewCard,
    ChatSession,
    ChatSessionSummary,
)


class ChatService:
    """把对话会话和消息保存在数据库中。"""

    def __init__(self):
        self._sessions: dict[UUID, ChatSession] = DocumentDict(
            "chat_sessions",
            model=ChatSession,
        )

    def list_sessions(self, project_id: UUID) -> List[ChatSessionSummary]:
        sessions = [
            session for session in self._sessions.values()
            if session.project_id == project_id
        ]
        sessions.sort(key=lambda item: item.updated_at, reverse=True)
        return [self._summary(session) for session in sessions]

    def list_all_sessions(self) -> List[ChatSessionSummary]:
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda item: item.updated_at, reverse=True)
        return [self._summary(session) for session in sessions]

    def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        return self._sessions.get(session_id)

    def append_exchange(
        self,
        *,
        session_id: UUID,
        project_id: UUID,
        user_content: str,
        user_sender: str,
        agent_content: str,
        agent_status: str,
        knowledge_results: list,
        classification: Optional[dict] = None,
        knowledge_blocked: bool = False,
    ) -> ChatSession:
        """写入一轮用户消息和 Agent 回复。"""
        now = datetime.utcnow()
        session = self._sessions.get(session_id)
        if session is None:
            title = " ".join(user_content.split()) or "新会话"
            if len(title) > 28:
                title = title[:28] + "…"
            session = ChatSession(
                id=session_id,
                project_id=project_id,
                title=title,
                created_at=now,
            )
        elif session.project_id != project_id:
            project_id = session.project_id

        hits = []
        for item in knowledge_results or []:
            if not isinstance(item, dict):
                continue
            try:
                hits.append(ChatKnowledgeHit(
                    title=str(item.get("title") or "未命名文档"),
                    snippet=str(item.get("snippet") or ""),
                    score=float(item.get("score") or 0),
                    knowledge_base_name=str(item.get("knowledge_base_name") or ""),
                    document_id=None if item.get("document_id") is None else str(item.get("document_id")),
                ))
            except (TypeError, ValueError):
                continue
        user_message = ChatMessage(
            role="user",
            content=user_content,
            sender=user_sender or "我",
            created_at=now,
        )
        parsed_classification = None
        if isinstance(classification, dict) and classification.get("type"):
            parsed_classification = ChatClassification(
                type=str(classification.get("type")),
                priority=str(classification.get("priority") or "medium"),
                title=str(classification.get("title") or ""),
                ticket_id=None if not classification.get("ticket_id") else str(classification.get("ticket_id")),
            )
        agent_message = ChatMessage(
            role="agent",
            content=agent_content,
            sender="Lead Agent",
            status=agent_status,
            knowledge_results=hits,
            classification=parsed_classification,
            knowledge_blocked=knowledge_blocked,
            created_at=now,
        )
        session.messages = [*session.messages, user_message, agent_message]
        session.updated_at = now
        self._sessions[session.id] = session
        return session

    def record_ticket(self, session_id: UUID, ticket_id: str) -> Optional[ChatSession]:
        """把已拦截的对话改成已提交，并写上工单号。"""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        marker = "补齐项目资料和知识库后才能提交需求。"
        replacement = f"需求已提交到 Review 工作台，工单 {ticket_id}。"
        changed = False
        for message in session.messages:
            if marker in message.content:
                message.content = message.content.replace(marker, replacement)
                changed = True
            if message.classification is not None and not message.classification.ticket_id:
                message.classification.ticket_id = ticket_id
                changed = True
        if not changed:
            return session
        session.updated_at = datetime.utcnow()
        self._sessions[session.id] = session
        return session

    def append_review_card(
        self,
        session_id: UUID,
        *,
        review_id: UUID,
        item_type: str,
        title: str,
        summary: str,
        content: str,
        root_cause: str = "",
        files: Optional[list] = None,
        due_at: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """在对话中追加一张审批卡片。同一审核不重复追加。"""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        review_key = str(review_id)
        for message in session.messages:
            if message.review and message.review.review_id == review_key:
                return session
        now = datetime.utcnow()
        session.messages = [
            *session.messages,
            ChatMessage(
                role="agent",
                content=content,
                sender="Lead Agent",
                status="complete",
                review=ChatReviewCard(
                    review_id=review_key,
                    item_type=item_type,
                    title=title,
                    status="pending",
                    summary=summary,
                    root_cause=root_cause,
                    files=list(files or []),
                    due_at=due_at,
                ),
                created_at=now,
            ),
        ]
        session.updated_at = now
        self._sessions[session.id] = session
        return session

    def mark_review(self, session_id: UUID, review_id: UUID, status: str) -> None:
        """同步对话卡片上的审核状态。"""
        session = self._sessions.get(session_id)
        if session is None:
            return
        review_key = str(review_id)
        changed = False
        for message in session.messages:
            if message.review and message.review.review_id == review_key:
                message.review.status = status
                changed = True
        if changed:
            session.updated_at = datetime.utcnow()
            self._sessions[session.id] = session

    def append_note(self, session_id: UUID, content: str, status: str = "complete") -> None:
        """追加一条没有审批卡片的 Agent 说明。"""
        session = self._sessions.get(session_id)
        if session is None:
            return
        now = datetime.utcnow()
        session.messages = [
            *session.messages,
            ChatMessage(
                role="agent",
                content=content,
                sender="Lead Agent",
                status=status,
                created_at=now,
            ),
        ]
        session.updated_at = now
        self._sessions[session.id] = session

    def _summary(self, session: ChatSession) -> ChatSessionSummary:
        status = "complete"
        for message in reversed(session.messages):
            if message.review and message.review.status in {"pending", "in_review"}:
                status = "pending"
                break
            if message.role == "agent" and message.review is None:
                status = "error" if message.status == "error" else "complete"
                break
        return ChatSessionSummary(
            id=session.id,
            project_id=session.project_id,
            title=session.title,
            message_count=len(session.messages),
            status=status,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


chat_service = ChatService()
