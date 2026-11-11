"""HITL (Human-In-The-Loop) 审核中间件服务"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from ..db import DocumentDict
from ..models.review import (
    ReviewItem,
    ReviewItemCreate,
    ReviewItemType,
    ReviewStatus,
    ReviewPriority,
    ReviewComment,
    ReviewDecision,
    ReviewDecisionType,
    ReviewFilters,
    ReviewHistoryEntry,
)

if TYPE_CHECKING:
    from .notification_service import NotificationService


class HITLService:
    """HITL 审核中间件服务

    负责管理审核项的创建、提交、审批、拒绝和修改请求等操作。
    审核数据保存在数据库中。
    """

    def __init__(self):
        self._review_items: Dict[UUID, ReviewItem] = DocumentDict(
            "review_items",
            model=ReviewItem,
        )
        self._project_reviews: Dict[UUID, List[UUID]] = {}
        self._item_reviews: Dict[str, UUID] = {}
        for item in self._review_items.values():
            self._project_reviews.setdefault(item.project_id, []).append(item.id)
            item_type = item.item_type.value if hasattr(item.item_type, "value") else item.item_type
            self._item_reviews[f"{item_type}:{item.item_id}"] = item.id
        self._history: Dict[UUID, List[ReviewHistoryEntry]] = DocumentDict(
            "review_history",
            loader=lambda payload: [ReviewHistoryEntry.model_validate(item) for item in payload],
        )
        self._notification_service: Optional["NotificationService"] = None
        self._default_timeout_hours: int = 24
        self._warning_threshold_hours: int = 4

    def set_notification_service(self, notification_service: "NotificationService"):
        """设置通知服务引用"""
        self._notification_service = notification_service

    def create_review_item(
        self,
        item_type: ReviewItemType,
        item_id: UUID,
        data: ReviewItemCreate,
    ) -> ReviewItem:
        """创建待审项

        Args:
            item_type: 审核项类型
            item_id: 关联对象 ID
            data: 创建数据

        Returns:
            创建的审核项
        """
        review_key = f"{item_type.value}:{item_id}"

        if review_key in self._item_reviews:
            existing_id = self._item_reviews[review_key]
            if existing_id in self._review_items:
                existing = self._review_items[existing_id]
                if existing.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
                    return existing

        due_at = data.due_at
        if not due_at:
            due_at = datetime.utcnow() + timedelta(hours=self._default_timeout_hours)

        review_item = ReviewItem(
            id=uuid4(),
            item_type=item_type,
            item_id=item_id,
            project_id=data.project_id,
            requirement_id=data.requirement_id,
            session_id=data.session_id,
            title=data.title,
            description=data.description,
            status=ReviewStatus.PENDING,
            priority=data.priority,
            due_at=due_at,
        )

        self._review_items[review_item.id] = review_item

        if data.project_id not in self._project_reviews:
            self._project_reviews[data.project_id] = []
        self._project_reviews[data.project_id].append(review_item.id)

        self._item_reviews[review_key] = review_item.id

        self._add_history_entry(
            review_item.id,
            action="created",
            actor="system",
            details=f"审核项创建: {review_item.title}",
        )

        if self._notification_service:
            self._notification_service.notify_review_created(review_item)

        return review_item

    def submit_for_review(
        self,
        item_type: ReviewItemType,
        item_id: UUID,
        submitter: str = "system",
    ) -> Optional[ReviewItem]:
        """提交审核

        Args:
            item_type: 审核项类型
            item_id: 关联对象 ID
            submitter: 提交人

        Returns:
            审核项，不存在返回 None
        """
        review_key = f"{item_type.value}:{item_id}"
        review_id = self._item_reviews.get(review_key)

        if not review_id or review_id not in self._review_items:
            return None

        review_item = self._review_items[review_id]

        if review_item.status != ReviewStatus.PENDING:
            return review_item

        review_item.status = ReviewStatus.IN_REVIEW
        review_item.updated_at = datetime.utcnow()

        self._add_history_entry(
            review_item.id,
            action="submitted",
            actor=submitter,
            details="提交审核",
        )

        return review_item

    def approve(
        self,
        review_id: UUID,
        reviewer: str,
        reason: str = "",
    ) -> Optional[ReviewItem]:
        """通过审核

        Args:
            review_id: 审核项 ID
            reviewer: 审核人
            reason: 通过理由

        Returns:
            更新后的审核项，不存在返回 None
        """
        review_item = self._review_items.get(review_id)
        if not review_item:
            return None

        if review_item.status not in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
            return review_item

        decision = ReviewDecision(
            id=uuid4(),
            review_item_id=review_id,
            decision=ReviewDecisionType.APPROVE,
            reviewer=reviewer,
            reason=reason,
        )

        review_item.decisions.append(decision)
        review_item.status = ReviewStatus.APPROVED
        review_item.reviewer = reviewer
        review_item.updated_at = datetime.utcnow()

        self._add_history_entry(
            review_id,
            action="approved",
            actor=reviewer,
            details=f"审核通过: {reason}" if reason else "审核通过",
        )

        if self._notification_service:
            self._notification_service.notify_review_decision(review_item, decision)

        return review_item

    def supersede(self, review_id: UUID, reason: str) -> Optional[ReviewItem]:
        """作废仍在审核中的方案，不关闭需求。"""
        review_item = self._review_items.get(review_id)
        if not review_item:
            return None
        if review_item.status not in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
            return review_item

        review_item.status = ReviewStatus.REJECTED
        review_item.updated_at = datetime.utcnow()
        self._review_items[review_item.id] = review_item
        self._add_history_entry(
            review_id,
            action="superseded",
            actor="system",
            details=reason,
        )
        return review_item

    def reject(
        self,
        review_id: UUID,
        reviewer: str,
        reason: str,
    ) -> Optional[ReviewItem]:
        """拒绝审核

        Args:
            review_id: 审核项 ID
            reviewer: 审核人
            reason: 拒绝理由

        Returns:
            更新后的审核项，不存在返回 None
        """
        review_item = self._review_items.get(review_id)
        if not review_item:
            return None

        if review_item.status not in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
            return review_item

        decision = ReviewDecision(
            id=uuid4(),
            review_item_id=review_id,
            decision=ReviewDecisionType.REJECT,
            reviewer=reviewer,
            reason=reason,
        )

        review_item.decisions.append(decision)
        review_item.status = ReviewStatus.REJECTED
        review_item.reviewer = reviewer
        review_item.updated_at = datetime.utcnow()

        self._add_history_entry(
            review_id,
            action="rejected",
            actor=reviewer,
            details=f"审核拒绝: {reason}",
        )

        if self._notification_service:
            self._notification_service.notify_review_decision(review_item, decision)

        return review_item

    def request_revision(
        self,
        review_id: UUID,
        reviewer: str,
        comments: str,
    ) -> Optional[ReviewItem]:
        """要求修改

        Args:
            review_id: 审核项 ID
            reviewer: 审核人
            comments: 修改意见

        Returns:
            更新后的审核项，不存在返回 None
        """
        review_item = self._review_items.get(review_id)
        if not review_item:
            return None

        if review_item.status not in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
            return review_item

        decision = ReviewDecision(
            id=uuid4(),
            review_item_id=review_id,
            decision=ReviewDecisionType.REQUEST_REVISION,
            reviewer=reviewer,
            reason=comments,
        )

        review_item.decisions.append(decision)
        review_item.status = ReviewStatus.REVISION_REQUESTED
        review_item.reviewer = reviewer
        review_item.updated_at = datetime.utcnow()

        comment = ReviewComment(
            id=uuid4(),
            review_item_id=review_id,
            author=reviewer,
            content=f"[修改请求] {comments}",
        )
        review_item.comments.append(comment)

        self._add_history_entry(
            review_id,
            action="revision_requested",
            actor=reviewer,
            details=f"要求修改: {comments}",
        )

        if self._notification_service:
            self._notification_service.notify_review_decision(review_item, decision)

        return review_item

    def add_comment(
        self,
        review_id: UUID,
        author: str,
        content: str,
    ) -> Optional[ReviewComment]:
        """添加评论

        Args:
            review_id: 审核项 ID
            author: 评论作者
            content: 评论内容

        Returns:
            创建的评论，审核项不存在返回 None
        """
        review_item = self._review_items.get(review_id)
        if not review_item:
            return None

        comment = ReviewComment(
            id=uuid4(),
            review_item_id=review_id,
            author=author,
            content=content,
        )

        review_item.comments.append(comment)
        review_item.updated_at = datetime.utcnow()

        self._add_history_entry(
            review_id,
            action="commented",
            actor=author,
            details=f"添加评论: {content[:100]}..." if len(content) > 100 else f"添加评论: {content}",
        )

        return comment

    def get_comments(
        self,
        review_id: UUID,
    ) -> List[ReviewComment]:
        """获取评论列表

        Args:
            review_id: 审核项 ID

        Returns:
            评论列表
        """
        review_item = self._review_items.get(review_id)
        if not review_item:
            return []

        return review_item.comments

    def get_review_item(self, review_id: UUID) -> Optional[ReviewItem]:
        """获取审核项详情

        Args:
            review_id: 审核项 ID

        Returns:
            审核项，不存在返回 None
        """
        return self._review_items.get(review_id)

    def find_by_item(self, item_type: ReviewItemType, item_id: UUID) -> Optional[ReviewItem]:
        """按关联对象查找最近一次审核。"""
        review_id = self._item_reviews.get(f"{item_type.value}:{item_id}")
        if not review_id:
            return None
        return self._review_items.get(review_id)

    def get_pending_reviews(
        self,
        project_id: Optional[UUID] = None,
        item_type: Optional[ReviewItemType] = None,
        reviewer: Optional[str] = None,
        filters: Optional[ReviewFilters] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[ReviewItem]:
        """获取待审列表。列出前先处理已经到期的审核。"""
        self.check_timeout_escalation()
        if project_id:
            review_ids = self._project_reviews.get(project_id, [])
            reviews = [
                self._review_items[rid] for rid in review_ids
                if rid in self._review_items
            ]
        else:
            reviews = list(self._review_items.values())

        pending_statuses = [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]
        reviews = [r for r in reviews if r.status in pending_statuses]

        if item_type:
            reviews = [r for r in reviews if r.item_type == item_type]

        if reviewer:
            reviews = [
                r for r in reviews
                if r.reviewer == reviewer or r.reviewer is None
            ]

        if filters:
            if filters.status:
                reviews = [r for r in reviews if r.status == filters.status]
            if filters.priority:
                reviews = [r for r in reviews if r.priority == filters.priority]
            if filters.item_type:
                reviews = [r for r in reviews if r.item_type == filters.item_type]
            if filters.reviewer:
                reviews = [r for r in reviews if r.reviewer == filters.reviewer]

        priority_order = {
            ReviewPriority.URGENT: 0,
            ReviewPriority.HIGH: 1,
            ReviewPriority.MEDIUM: 2,
            ReviewPriority.LOW: 3,
        }
        reviews.sort(key=lambda x: (priority_order.get(x.priority, 2), x.created_at))

        start = (page - 1) * page_size
        end = start + page_size

        return reviews[start:end]

    def count_pending_reviews(
        self,
        project_id: Optional[UUID] = None,
        item_type: Optional[ReviewItemType] = None,
        reviewer: Optional[str] = None,
        filters: Optional[ReviewFilters] = None,
    ) -> int:
        """统计待审数量"""
        if project_id:
            review_ids = self._project_reviews.get(project_id, [])
            reviews = [
                self._review_items[rid] for rid in review_ids
                if rid in self._review_items
            ]
        else:
            reviews = list(self._review_items.values())

        pending_statuses = [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]
        reviews = [r for r in reviews if r.status in pending_statuses]

        if item_type:
            reviews = [r for r in reviews if r.item_type == item_type]

        if reviewer:
            reviews = [
                r for r in reviews
                if r.reviewer == reviewer or r.reviewer is None
            ]

        if filters:
            if filters.status:
                reviews = [r for r in reviews if r.status == filters.status]
            if filters.priority:
                reviews = [r for r in reviews if r.priority == filters.priority]
            if filters.item_type:
                reviews = [r for r in reviews if r.item_type == filters.item_type]
            if filters.reviewer:
                reviews = [r for r in reviews if r.reviewer == filters.reviewer]

        return len(reviews)

    def get_review_history(self, item_id: UUID) -> List[ReviewHistoryEntry]:
        """获取审核历史

        Args:
            item_id: 审核项 ID 或关联对象 ID

        Returns:
            历史记录列表
        """
        if item_id in self._history:
            return sorted(
                self._history[item_id],
                key=lambda x: x.created_at,
                reverse=True,
            )

        for review_key, review_id in self._item_reviews.items():
            if str(item_id) in review_key:
                return sorted(
                    self._history.get(review_id, []),
                    key=lambda x: x.created_at,
                    reverse=True,
                )

        return []

    def check_timeout_escalation(self) -> List[ReviewItem]:
        """检查超时升级

        Returns:
            需要升级的审核项列表
        """
        now = datetime.utcnow()
        warning_threshold = now + timedelta(hours=self._warning_threshold_hours)
        escalation_items = []

        for review_item in self._review_items.values():
            if review_item.status not in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
                continue

            if review_item.due_at:
                if review_item.due_at <= now:
                    if review_item.priority != ReviewPriority.URGENT:
                        review_item.priority = ReviewPriority.URGENT
                        review_item.updated_at = now

                        self._add_history_entry(
                            review_item.id,
                            action="escalated",
                            actor="system",
                            details="审核超时，优先级升级为紧急",
                        )

                        escalation_items.append(review_item)
                        if self._notification_service:
                            self._notification_service.notify_timeout_escalation(review_item)

                elif review_item.due_at <= warning_threshold:
                    if self._notification_service:
                        self._notification_service.notify_timeout_warning(review_item)

        return escalation_items

    def assign_reviewer(
        self,
        review_id: UUID,
        reviewer: str,
        assigner: str = "system",
    ) -> Optional[ReviewItem]:
        """分配审核人

        Args:
            review_id: 审核项 ID
            reviewer: 审核人
            assigner: 分配人

        Returns:
            更新后的审核项
        """
        review_item = self._review_items.get(review_id)
        if not review_item:
            return None

        review_item.reviewer = reviewer
        review_item.updated_at = datetime.utcnow()

        self._add_history_entry(
            review_id,
            action="assigned",
            actor=assigner,
            details=f"分配审核人: {reviewer}",
        )

        if self._notification_service:
            self._notification_service.notify_review_assigned(review_item, reviewer)

        return review_item

    def resubmit_for_review(
        self,
        review_id: UUID,
        submitter: str = "system",
    ) -> Optional[ReviewItem]:
        """重新提交审核（修改后）

        Args:
            review_id: 审核项 ID
            submitter: 提交人

        Returns:
            更新后的审核项
        """
        review_item = self._review_items.get(review_id)
        if not review_item:
            return None

        if review_item.status != ReviewStatus.REVISION_REQUESTED:
            return review_item

        review_item.status = ReviewStatus.IN_REVIEW
        review_item.updated_at = datetime.utcnow()

        self._add_history_entry(
            review_item.id,
            action="resubmitted",
            actor=submitter,
            details="修改后重新提交审核",
        )

        return review_item

    def _add_history_entry(
        self,
        review_id: UUID,
        action: str,
        actor: str,
        details: str = "",
    ):
        """添加历史记录"""
        entry = ReviewHistoryEntry(
            id=uuid4(),
            action=action,
            actor=actor,
            details=details,
            created_at=datetime.utcnow(),
        )
        entries = list(self._history.get(review_id, []))
        entries.append(entry)
        self._history[review_id] = entries

    def get_review_statistics(
        self,
        project_id: Optional[UUID] = None,
    ) -> dict:
        """获取审核统计

        Args:
            project_id: 项目 ID（可选）

        Returns:
            统计数据
        """
        if project_id:
            review_ids = self._project_reviews.get(project_id, [])
            reviews = [
                self._review_items[rid] for rid in review_ids
                if rid in self._review_items
            ]
        else:
            reviews = list(self._review_items.values())

        by_status = {}
        for s in ReviewStatus:
            by_status[s.value] = len([r for r in reviews if r.status == s])

        by_type = {}
        for t in ReviewItemType:
            by_type[t.value] = len([r for r in reviews if r.item_type == t])

        by_priority = {}
        for p in ReviewPriority:
            by_priority[p.value] = len([r for r in reviews if r.priority == p])

        pending_count = by_status.get("pending", 0) + by_status.get("in_review", 0)

        overdue_count = 0
        now = datetime.utcnow()
        for r in reviews:
            if r.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
                if r.due_at and r.due_at <= now:
                    overdue_count += 1

        return {
            "total": len(reviews),
            "pending": pending_count,
            "overdue": overdue_count,
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
        }


hitl_service = HITLService()
