import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { ReviewItem, ReviewComment, ReviewDecision, ReviewItemType } from '../types'
import { reviewService } from '../services'
import {
  ReviewStatusBadge,
  ReviewActions,
  CommentSection,
  ReviewTimeline,
  DecisionModal,
} from '../components/Reviews'
import { PriorityBadge } from '../components/Requirements'

const typeConfig: Record<ReviewItemType, { icon: string; label: string }> = {
  solution: { icon: '📋', label: '方案审核' },
  code: { icon: '💻', label: '代码审核' },
  test: { icon: '🧪', label: '测试审核' },
}

const mockReview: ReviewItem = {
  id: '1',
  item_type: 'solution',
  item_id: 'sol-1',
  project_id: '1',
  title: '用户登录超时问题修复方案',
  description: `## 问题描述
用户反馈登录后约10分钟就会被强制登出，需要重新登录。

## 原因分析
1. Session 超时时间设置过短（默认 10 分钟）
2. Token 刷新机制存在问题，前端未正确处理 refresh token

## 修复方案
1. 将 Session 超时时间延长至 30 分钟
2. 实现自动 Token 刷新机制
3. 添加用户活动检测，有活动时自动延长会话

## 影响范围
- 用户服务模块
- 认证中间件
- 前端 axios 拦截器

## 测试计划
1. 单元测试：Token 刷新逻辑
2. 集成测试：完整登录流程
3. 压力测试：并发场景下的会话管理`,
  status: 'pending',
  priority: 'high',
  reviewer: '张三',
  comments_count: 3,
  created_at: new Date(Date.now() - 2 * 3600000).toISOString(),
  due_at: new Date(Date.now() + 4 * 3600000).toISOString(),
}

const mockComments: ReviewComment[] = [
  {
    id: '1',
    review_item_id: '1',
    author: '李四',
    content: '方案整体思路清晰，但建议补充一下并发情况下的处理逻辑。',
    created_at: new Date(Date.now() - 1 * 3600000).toISOString(),
  },
  {
    id: '2',
    review_item_id: '1',
    author: '王五',
    content: 'Token 刷新机制需要考虑网络延迟的情况，建议增加重试机制。',
    created_at: new Date(Date.now() - 30 * 60000).toISOString(),
  },
  {
    id: '3',
    review_item_id: '1',
    author: '张三',
    content: '已补充并发处理和网络重试的说明，请查看更新版本。',
    created_at: new Date(Date.now() - 15 * 60000).toISOString(),
  },
]

const mockDecisions: ReviewDecision[] = []

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function isOverdue(dueAt?: string): boolean {
  if (!dueAt) return false
  return new Date(dueAt) < new Date()
}

export default function ReviewDetail() {
  const { reviewId } = useParams<{ reviewId: string }>()
  const navigate = useNavigate()
  const [review, setReview] = useState<ReviewItem | null>(null)
  const [comments, setComments] = useState<ReviewComment[]>([])
  const [decisions, setDecisions] = useState<ReviewDecision[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCommentsLoading, setIsCommentsLoading] = useState(true)
  const [modalType, setModalType] = useState<'approve' | 'reject' | 'revision' | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (reviewId) {
      loadReviewDetail(reviewId)
    }
  }, [reviewId])

  const loadReviewDetail = async (id: string) => {
    setIsLoading(true)
    setIsCommentsLoading(true)
    try {
      const [reviewData, commentsData, decisionsData] = await Promise.all([
        reviewService.getReviewDetail(id),
        reviewService.getComments(id),
        reviewService.getDecisions(id),
      ])
      setReview(reviewData)
      setComments(commentsData)
      setDecisions(decisionsData)
    } catch {
      console.log('Using mock data')
      setReview(mockReview)
      setComments(mockComments)
      setDecisions(mockDecisions)
    } finally {
      setIsLoading(false)
      setIsCommentsLoading(false)
    }
  }

  const handleAddComment = async (content: string) => {
    if (!reviewId) return
    try {
      const newComment = await reviewService.addComment(reviewId, content)
      setComments((prev) => [...prev, newComment])
    } catch {
      const mockComment: ReviewComment = {
        id: String(Date.now()),
        review_item_id: reviewId,
        author: '当前用户',
        content,
        created_at: new Date().toISOString(),
      }
      setComments((prev) => [...prev, mockComment])
    }
  }

  const handleDecision = async (reason: string) => {
    if (!reviewId || !modalType) return
    setIsSubmitting(true)

    try {
      let decision: ReviewDecision
      if (modalType === 'approve') {
        decision = await reviewService.approve(reviewId, reason)
      } else if (modalType === 'reject') {
        decision = await reviewService.reject(reviewId, reason)
      } else {
        decision = await reviewService.requestRevision(reviewId, reason)
      }
      setDecisions((prev) => [decision, ...prev])

      const statusMap = {
        approve: 'approved',
        reject: 'rejected',
        revision: 'revision_requested',
      } as const
      setReview((prev) => prev ? { ...prev, status: statusMap[modalType] } : null)
    } catch {
      const mockDecision: ReviewDecision = {
        id: String(Date.now()),
        review_item_id: reviewId,
        decision: modalType === 'approve' ? 'approved' : modalType === 'reject' ? 'rejected' : 'revision_requested',
        reviewer: '当前用户',
        reason,
        created_at: new Date().toISOString(),
      }
      setDecisions((prev) => [mockDecision, ...prev])

      const statusMap = {
        approve: 'approved',
        reject: 'rejected',
        revision: 'revision_requested',
      } as const
      setReview((prev) => prev ? { ...prev, status: statusMap[modalType] } : null)
    } finally {
      setIsSubmitting(false)
      setModalType(null)
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 bg-gray-50 min-h-full flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent" />
          <p className="mt-4 text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  if (!review) {
    return (
      <div className="p-6 bg-gray-50 min-h-full flex items-center justify-center">
        <div className="text-center">
          <span className="text-4xl">🔍</span>
          <p className="mt-4 text-gray-500">审核项不存在</p>
          <button
            onClick={() => navigate('/reviews')}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm"
          >
            返回列表
          </button>
        </div>
      </div>
    )
  }

  const typeInfo = typeConfig[review.item_type]
  const overdue = isOverdue(review.due_at)
  const canReview = review.status === 'pending' || review.status === 'in_review'

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-5xl mx-auto">
        <button
          onClick={() => navigate('/reviews')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回审核列表
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className={`bg-white rounded-xl border p-6 ${overdue ? 'border-red-300' : 'border-gray-200'}`}>
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{typeInfo.icon}</span>
                  <span className="text-sm font-medium text-gray-500 bg-gray-100 px-3 py-1 rounded-lg">
                    {typeInfo.label}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <PriorityBadge priority={review.priority} />
                  <ReviewStatusBadge status={review.status} />
                </div>
              </div>

              <h1 className="text-xl font-semibold text-gray-800 mb-4">
                {review.title}
              </h1>

              <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
                <span>创建于: {formatDate(review.created_at)}</span>
                {review.due_at && (
                  <span className={overdue ? 'text-red-500 font-medium' : ''}>
                    {overdue ? '⚠️ 已超时' : `截止: ${formatDate(review.due_at)}`}
                  </span>
                )}
                {review.reviewer && <span>审核人: {review.reviewer}</span>}
              </div>

              <div className="prose prose-sm max-w-none">
                <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
                  {review.description}
                </div>
              </div>

              {canReview && (
                <div className="mt-6 pt-6 border-t border-gray-100">
                  <ReviewActions
                    onApprove={() => setModalType('approve')}
                    onReject={() => setModalType('reject')}
                    onRequestRevision={() => setModalType('revision')}
                    disabled={isSubmitting}
                  />
                </div>
              )}
            </div>

            <CommentSection
              comments={comments}
              onAddComment={handleAddComment}
              isLoading={isCommentsLoading}
            />
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-4">📊 审核信息</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">类型</span>
                  <span className="font-medium">{typeInfo.icon} {typeInfo.label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">状态</span>
                  <ReviewStatusBadge status={review.status} size="sm" />
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">优先级</span>
                  <PriorityBadge priority={review.priority} size="sm" />
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">评论数</span>
                  <span className="font-medium">{comments.length}</span>
                </div>
                {review.reviewer && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">审核人</span>
                    <span className="font-medium">{review.reviewer}</span>
                  </div>
                )}
              </div>
            </div>

            <ReviewTimeline decisions={decisions} createdAt={review.created_at} />
          </div>
        </div>
      </div>

      {modalType && (
        <DecisionModal
          isOpen={true}
          type={modalType}
          onClose={() => setModalType(null)}
          onConfirm={handleDecision}
        />
      )}
    </div>
  )
}
