# Review 工作台代码

文件：frontend/src/pages/Reviews.tsx，frontend/src/pages/ReviewDetail.tsx，backend/src/api/routes/reviews.py。
症状：Review 工作台看不到待审核数据，无法查看审批历史，通过、拒绝、要求修改没有生效，审核页方案 Markdown 不渲染。

列表只调用 frontend/src/services/reviewService.ts 的 getPendingReviews，对应 GET /api/v1/reviews/pending。后端 list_pending_reviews、get_review、approve_review、reject_review、request_revision、get_review_history 在 reviews.py。待审状态只有 pending 和 in_review，已通过的历史不会出现在这个列表。数据在 backend/src/services/hitl_service.py 的 get_pending_reviews、approve、reject、request_revision、supersede。方案进入审核在 backend/src/services/workflow_service.py 的 _queue_solution_review。同一需求多份待审核方案由 solution_service.collapse_pending_solutions 只留最新一份。详情页用 ReactMarkdown 渲染方案正文。卡片：frontend/src/components/Reviews/ReviewCard.tsx、ReviewActions.tsx、DecisionModal.tsx。
