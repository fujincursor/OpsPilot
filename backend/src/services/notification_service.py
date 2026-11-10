"""通知服务"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..db import DocumentDict
from ..models.review import (
    ReviewItem,
    ReviewDecision,
    ReviewDecisionType,
    Notification,
    NotificationType,
)


class NotificationService:
    """通知服务

    负责发送和管理审核相关的通知。通知保存在数据库中。
    """

    def __init__(self):
        self._notifications: Dict[UUID, Notification] = DocumentDict(
            "notifications",
            model=Notification,
        )
        self._user_notifications: Dict[str, List[UUID]] = {}
        for notification in self._notifications.values():
            self._user_notifications.setdefault(notification.user_id, []).append(notification.id)

    def notify_review_created(self, review_item: ReviewItem) -> Notification:
        """通知新审核项创建

        Args:
            review_item: 审核项

        Returns:
            创建的通知
        """
        notification = Notification(
            id=uuid4(),
            user_id="all_reviewers",
            type=NotificationType.REVIEW_CREATED,
            title="新的审核项待处理",
            content=f"[{review_item.item_type.value}] {review_item.title} 需要审核",
            review_item_id=review_item.id,
        )

        self._store_notification(notification)

        if review_item.reviewer:
            self._create_user_notification(
                user_id=review_item.reviewer,
                notification_type=NotificationType.REVIEW_ASSIGNED,
                title="您有新的审核任务",
                content=f"[{review_item.item_type.value}] {review_item.title} 已分配给您",
                review_item_id=review_item.id,
            )

        return notification

    def notify_review_assigned(
        self,
        review_item: ReviewItem,
        reviewer: str,
    ) -> Notification:
        """通知审核分配

        Args:
            review_item: 审核项
            reviewer: 审核人

        Returns:
            创建的通知
        """
        return self._create_user_notification(
            user_id=reviewer,
            notification_type=NotificationType.REVIEW_ASSIGNED,
            title="审核任务分配",
            content=f"[{review_item.item_type.value}] {review_item.title} 已分配给您审核",
            review_item_id=review_item.id,
        )

    def notify_review_decision(
        self,
        review_item: ReviewItem,
        decision: ReviewDecision,
    ) -> Notification:
        """通知审核结果

        Args:
            review_item: 审核项
            decision: 审核决定

        Returns:
            创建的通知
        """
        type_map = {
            ReviewDecisionType.APPROVE: NotificationType.REVIEW_APPROVED,
            ReviewDecisionType.REJECT: NotificationType.REVIEW_REJECTED,
            ReviewDecisionType.REQUEST_REVISION: NotificationType.REVIEW_REVISION_REQUESTED,
        }

        title_map = {
            ReviewDecisionType.APPROVE: "审核已通过",
            ReviewDecisionType.REJECT: "审核被拒绝",
            ReviewDecisionType.REQUEST_REVISION: "审核要求修改",
        }

        content_map = {
            ReviewDecisionType.APPROVE: f"[{review_item.item_type.value}] {review_item.title} 已通过审核",
            ReviewDecisionType.REJECT: f"[{review_item.item_type.value}] {review_item.title} 被拒绝: {decision.reason}",
            ReviewDecisionType.REQUEST_REVISION: f"[{review_item.item_type.value}] {review_item.title} 需要修改: {decision.reason}",
        }

        notification = Notification(
            id=uuid4(),
            user_id="item_owner",
            type=type_map.get(decision.decision, NotificationType.REVIEW_APPROVED),
            title=title_map.get(decision.decision, "审核决定"),
            content=content_map.get(decision.decision, ""),
            review_item_id=review_item.id,
        )

        self._store_notification(notification)
        return notification

    def notify_timeout_warning(self, review_item: ReviewItem) -> Notification:
        """超时警告通知

        Args:
            review_item: 审核项

        Returns:
            创建的通知
        """
        content = f"[{review_item.item_type.value}] {review_item.title} 即将超时"
        if review_item.due_at:
            content += f"，截止时间: {review_item.due_at.strftime('%Y-%m-%d %H:%M')}"

        notification = Notification(
            id=uuid4(),
            user_id=review_item.reviewer or "all_reviewers",
            type=NotificationType.REVIEW_TIMEOUT_WARNING,
            title="审核即将超时",
            content=content,
            review_item_id=review_item.id,
        )

        self._store_notification(notification)
        return notification

    def notify_timeout_escalation(self, review_item: ReviewItem) -> None:
        """超时后通知管理员。"""
        from .user_service import UserService

        content = f"[{review_item.item_type.value}] {review_item.title} 已超过 24 小时未处理，优先级已升级。"
        admins = [user for user in UserService.list_all() if user.role.value == "admin" and user.is_active]
        recipients = admins or [None]
        for user in recipients:
            notification = Notification(
                id=uuid4(),
                user_id=user.id if user else "admin",
                type=NotificationType.REVIEW_TIMEOUT_WARNING,
                title="审核已超时并升级",
                content=content,
                review_item_id=review_item.id,
            )
            self._store_notification(notification)

    def notify_comment_added(
        self,
        review_item: ReviewItem,
        author: str,
        content: str,
    ) -> Notification:
        """通知新评论

        Args:
            review_item: 审核项
            author: 评论作者
            content: 评论内容

        Returns:
            创建的通知
        """
        preview = content[:100] + "..." if len(content) > 100 else content

        notification = Notification(
            id=uuid4(),
            user_id="item_participants",
            type=NotificationType.REVIEW_COMMENTED,
            title=f"{author} 添加了评论",
            content=f"[{review_item.item_type.value}] {review_item.title}: {preview}",
            review_item_id=review_item.id,
        )

        self._store_notification(notification)
        return notification

    def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Notification]:
        """获取用户通知

        Args:
            user_id: 用户 ID
            unread_only: 只返回未读通知
            page: 页码
            page_size: 每页数量

        Returns:
            通知列表
        """
        notification_ids = self._user_notifications.get(user_id, [])

        all_notification_ids = (
            notification_ids +
            self._user_notifications.get("all_reviewers", []) +
            self._user_notifications.get("item_owner", []) +
            self._user_notifications.get("item_participants", [])
        )

        notifications = [
            self._notifications[nid] for nid in all_notification_ids
            if nid in self._notifications
        ]

        if unread_only:
            notifications = [n for n in notifications if not n.is_read]

        notifications.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return notifications[start:end]

    def count_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
    ) -> int:
        """统计通知数量"""
        notification_ids = self._user_notifications.get(user_id, [])

        all_notification_ids = (
            notification_ids +
            self._user_notifications.get("all_reviewers", []) +
            self._user_notifications.get("item_owner", []) +
            self._user_notifications.get("item_participants", [])
        )

        notifications = [
            self._notifications[nid] for nid in all_notification_ids
            if nid in self._notifications
        ]

        if unread_only:
            notifications = [n for n in notifications if not n.is_read]

        return len(notifications)

    def count_unread(self, user_id: str) -> int:
        """统计未读通知数量"""
        return self.count_notifications(user_id, unread_only=True)

    def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """标记通知为已读

        Args:
            notification_id: 通知 ID

        Returns:
            更新后的通知
        """
        notification = self._notifications.get(notification_id)
        if not notification:
            return None

        notification.is_read = True
        self._notifications[notification.id] = notification
        return notification

    def mark_all_as_read(self, user_id: str) -> int:
        """标记用户所有通知为已读

        Args:
            user_id: 用户 ID

        Returns:
            标记数量
        """
        count = 0
        notification_ids = self._user_notifications.get(user_id, [])

        for nid in notification_ids:
            if nid in self._notifications:
                notification = self._notifications[nid]
                if not notification.is_read:
                    notification.is_read = True
                    self._notifications[nid] = notification
                    count += 1

        return count

    def delete_notification(self, notification_id: UUID) -> bool:
        """删除通知

        Args:
            notification_id: 通知 ID

        Returns:
            是否删除成功
        """
        if notification_id not in self._notifications:
            return False

        notification = self._notifications[notification_id]
        del self._notifications[notification_id]

        if notification.user_id in self._user_notifications:
            self._user_notifications[notification.user_id] = [
                nid for nid in self._user_notifications[notification.user_id]
                if nid != notification_id
            ]

        return True

    def _store_notification(self, notification: Notification):
        """存储通知"""
        self._notifications[notification.id] = notification

        if notification.user_id not in self._user_notifications:
            self._user_notifications[notification.user_id] = []
        self._user_notifications[notification.user_id].append(notification.id)

    def _create_user_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        content: str,
        review_item_id: Optional[UUID] = None,
    ) -> Notification:
        """创建用户通知"""
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            review_item_id=review_item_id,
        )

        self._store_notification(notification)
        return notification

    def get_notification_statistics(self, user_id: str) -> dict:
        """获取通知统计

        Args:
            user_id: 用户 ID

        Returns:
            统计数据
        """
        notifications = self.get_notifications(user_id, page_size=1000)

        by_type = {}
        for t in NotificationType:
            by_type[t.value] = len([n for n in notifications if n.type == t])

        unread = len([n for n in notifications if not n.is_read])
        read = len([n for n in notifications if n.is_read])

        return {
            "total": len(notifications),
            "unread": unread,
            "read": read,
            "by_type": by_type,
        }


notification_service = NotificationService()
