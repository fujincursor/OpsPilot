"""HITL Review API"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...models.review import (
    ReviewItem,
    ReviewItemCreate,
    ReviewItemType,
    ReviewItemResponse,
    ReviewStatus,
    ReviewPriority,
    ReviewFilters,
    ReviewApproveRequest,
    ReviewRejectRequest,
    ReviewRevisionRequest,
    ReviewComment,
    ReviewCommentCreate,
    ReviewCommentResponse,
    ReviewHistoryResponse,
    Notification,
    NotificationResponse,
)
from ...services.hitl_service import hitl_service
from ...services.notification_service import notification_service

router = APIRouter()


@router.get(
    "/projects/{project_id}/reviews",
    response_model=ReviewItemResponse,
)
async def list_project_reviews(
    project_id: UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    item_type: Optional[ReviewItemType] = Query(None, description="审核项类型"),
    status: Optional[ReviewStatus] = Query(None, description="状态筛选"),
    priority: Optional[ReviewPriority] = Query(None, description="优先级筛选"),
    reviewer: Optional[str] = Query(None, description="审核人筛选"),
) -> ReviewItemResponse:
    """
    获取项目待审列表

    返回指定项目下的所有待审核项，支持多种筛选条件。
    结果按优先级和创建时间排序。

    - **project_id**: 项目 ID
    - **page**: 页码
    - **page_size**: 每页数量
    - **item_type**: 审核项类型 (solution/code/test)
    - **status**: 状态筛选 (pending/in_review/approved/rejected/revision_requested)
    - **priority**: 优先级筛选 (low/medium/high/urgent)
    - **reviewer**: 审核人筛选
    """
    filters = ReviewFilters(
        item_type=item_type,
        status=status,
        priority=priority,
        reviewer=reviewer,
    )

    reviews = hitl_service.get_pending_reviews(
        project_id=project_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    total = hitl_service.count_pending_reviews(
        project_id=project_id,
        filters=filters,
    )

    return ReviewItemResponse(
        items=reviews,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/reviews/pending",
    response_model=ReviewItemResponse,
)
async def list_pending_reviews(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    item_type: Optional[ReviewItemType] = Query(None, description="审核项类型"),
    priority: Optional[ReviewPriority] = Query(None, description="优先级筛选"),
    reviewer: Optional[str] = Query(None, description="审核人"),
) -> ReviewItemResponse:
    """
    获取当前用户待审列表

    返回所有待处理的审核项，可按类型和优先级筛选。
    如果指定 reviewer，则只返回分配给该审核人的项目。

    - **page**: 页码
    - **page_size**: 每页数量
    - **item_type**: 审核项类型 (solution/code/test)
    - **priority**: 优先级筛选 (low/medium/high/urgent)
    - **reviewer**: 审核人（可选）
    """
    filters = ReviewFilters(
        item_type=item_type,
        priority=priority,
        reviewer=reviewer,
    )

    reviews = hitl_service.get_pending_reviews(
        reviewer=reviewer,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    total = hitl_service.count_pending_reviews(
        reviewer=reviewer,
        filters=filters,
    )

    return ReviewItemResponse(
        items=reviews,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewItem,
)
async def get_review(review_id: UUID) -> ReviewItem:
    """
    获取审核详情

    返回审核项的完整信息，包括评论和决定历史。

    - **review_id**: 审核项 ID
    """
    review = hitl_service.get_review_item(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.post(
    "/reviews",
    response_model=ReviewItem,
    status_code=201,
)
async def create_review(data: ReviewItemCreate) -> ReviewItem:
    """
    创建审核项

    为指定对象创建新的审核项。如果已存在未完成的审核，则返回现有审核项。

    - **item_type**: 审核项类型 (solution/code/test)
    - **item_id**: 关联对象 ID
    - **project_id**: 项目 ID
    - **title**: 标题
    - **description**: 描述
    - **priority**: 优先级
    - **due_at**: 截止时间（可选）
    """
    review = hitl_service.create_review_item(
        item_type=data.item_type,
        item_id=data.item_id,
        data=data,
    )

    return review


@router.post(
    "/reviews/{review_id}/approve",
    response_model=ReviewItem,
)
async def approve_review(
    review_id: UUID,
    data: ReviewApproveRequest,
    reviewer: str = Query(..., description="审核人"),
) -> ReviewItem:
    """
    通过审核

    将审核项状态更新为已通过，并记录审核人和理由。

    - **review_id**: 审核项 ID
    - **reviewer**: 审核人
    - **reason**: 通过理由（可选）
    """
    review = hitl_service.approve(
        review_id=review_id,
        reviewer=reviewer,
        reason=data.reason,
    )

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.post(
    "/reviews/{review_id}/reject",
    response_model=ReviewItem,
)
async def reject_review(
    review_id: UUID,
    data: ReviewRejectRequest,
    reviewer: str = Query(..., description="审核人"),
) -> ReviewItem:
    """
    拒绝审核

    将审核项状态更新为已拒绝，需提供拒绝理由。

    - **review_id**: 审核项 ID
    - **reviewer**: 审核人
    - **reason**: 拒绝理由
    """
    review = hitl_service.reject(
        review_id=review_id,
        reviewer=reviewer,
        reason=data.reason,
    )

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.post(
    "/reviews/{review_id}/revision",
    response_model=ReviewItem,
)
async def request_revision(
    review_id: UUID,
    data: ReviewRevisionRequest,
    reviewer: str = Query(..., description="审核人"),
) -> ReviewItem:
    """
    要求修改

    将审核项状态更新为需要修改，并记录修改意见。

    - **review_id**: 审核项 ID
    - **reviewer**: 审核人
    - **comments**: 修改意见
    """
    review = hitl_service.request_revision(
        review_id=review_id,
        reviewer=reviewer,
        comments=data.comments,
    )

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.post(
    "/reviews/{review_id}/comments",
    response_model=ReviewComment,
    status_code=201,
)
async def add_comment(
    review_id: UUID,
    data: ReviewCommentCreate,
    author: str = Query(..., description="评论作者"),
) -> ReviewComment:
    """
    添加评论

    为审核项添加评论，支持讨论和沟通。

    - **review_id**: 审核项 ID
    - **author**: 评论作者
    - **content**: 评论内容
    """
    comment = hitl_service.add_comment(
        review_id=review_id,
        author=author,
        content=data.content,
    )

    if not comment:
        raise HTTPException(status_code=404, detail="Review not found")

    review = hitl_service.get_review_item(review_id)
    if review:
        notification_service.notify_comment_added(review, author, data.content)

    return comment


@router.get(
    "/reviews/{review_id}/comments",
    response_model=ReviewCommentResponse,
)
async def get_comments(review_id: UUID) -> ReviewCommentResponse:
    """
    获取评论列表

    返回审核项的所有评论，按时间正序排列。

    - **review_id**: 审核项 ID
    """
    review = hitl_service.get_review_item(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    comments = hitl_service.get_comments(review_id)

    return ReviewCommentResponse(
        items=comments,
        total=len(comments),
    )


@router.get(
    "/reviews/{review_id}/history",
    response_model=ReviewHistoryResponse,
)
async def get_review_history(review_id: UUID) -> ReviewHistoryResponse:
    """
    获取审核历史

    返回审核项的操作历史记录，包括创建、提交、审核决定等操作。

    - **review_id**: 审核项 ID
    """
    review = hitl_service.get_review_item(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    history = hitl_service.get_review_history(review_id)

    return ReviewHistoryResponse(
        items=history,
        total=len(history),
    )


@router.get(
    "/notifications",
    response_model=NotificationResponse,
)
async def get_notifications(
    user_id: str = Query(..., description="用户 ID"),
    unread_only: bool = Query(False, description="只返回未读通知"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> NotificationResponse:
    """
    获取通知列表

    返回用户的通知列表，支持筛选未读通知。

    - **user_id**: 用户 ID
    - **unread_only**: 只返回未读通知
    - **page**: 页码
    - **page_size**: 每页数量
    """
    notifications = notification_service.get_notifications(
        user_id=user_id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )

    total = notification_service.count_notifications(
        user_id=user_id,
        unread_only=unread_only,
    )

    unread_count = notification_service.count_unread(user_id)

    return NotificationResponse(
        items=notifications,
        total=total,
        unread_count=unread_count,
    )


@router.post(
    "/notifications/{notification_id}/read",
    response_model=Notification,
)
async def mark_notification_read(notification_id: UUID) -> Notification:
    """
    标记通知为已读

    - **notification_id**: 通知 ID
    """
    notification = notification_service.mark_as_read(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


@router.post(
    "/notifications/read-all",
)
async def mark_all_notifications_read(
    user_id: str = Query(..., description="用户 ID"),
) -> dict:
    """
    标记所有通知为已读

    - **user_id**: 用户 ID
    """
    count = notification_service.mark_all_as_read(user_id)
    return {"marked_count": count}


@router.get("/reviews/statistics")
async def get_review_statistics(
    project_id: Optional[UUID] = Query(None, description="项目 ID（可选）"),
) -> dict:
    """
    获取审核统计

    返回按状态、类型、优先级分组的统计数据。
    如果提供 project_id，则只统计该项目下的审核项。

    - **project_id**: 项目 ID（可选）
    """
    return hitl_service.get_review_statistics(project_id)


@router.post(
    "/reviews/{review_id}/assign",
    response_model=ReviewItem,
)
async def assign_reviewer(
    review_id: UUID,
    reviewer: str = Query(..., description="审核人"),
    assigner: str = Query("system", description="分配人"),
) -> ReviewItem:
    """
    分配审核人

    为审核项指定审核人。

    - **review_id**: 审核项 ID
    - **reviewer**: 审核人
    - **assigner**: 分配人
    """
    review = hitl_service.assign_reviewer(
        review_id=review_id,
        reviewer=reviewer,
        assigner=assigner,
    )

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.post(
    "/reviews/{review_id}/resubmit",
    response_model=ReviewItem,
)
async def resubmit_review(
    review_id: UUID,
    submitter: str = Query("system", description="提交人"),
) -> ReviewItem:
    """
    重新提交审核

    在修改完成后重新提交审核（仅限状态为 revision_requested 的审核项）。

    - **review_id**: 审核项 ID
    - **submitter**: 提交人
    """
    review = hitl_service.resubmit_for_review(
        review_id=review_id,
        submitter=submitter,
    )

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status == ReviewStatus.REVISION_REQUESTED:
        raise HTTPException(
            status_code=400,
            detail="Can only resubmit reviews with revision_requested status",
        )

    return review


@router.post("/reviews/check-timeouts")
async def check_review_timeouts() -> dict:
    """
    检查审核超时

    检查所有待审核项是否超时，并执行优先级升级。
    返回被升级的审核项列表。

    此接口通常由定时任务调用。
    """
    escalated = hitl_service.check_timeout_escalation()
    return {
        "escalated_count": len(escalated),
        "escalated_ids": [str(r.id) for r in escalated],
    }
