import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { BugFixSolution, CodeGenTask, FeatureDesignSolution, ReviewItem, ReviewComment, ReviewDecision, ReviewItemType, TestTask } from '../types'
import { codegenService, reviewService, solutionService, testService } from '../services'
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
  const [solutionBody, setSolutionBody] = useState<BugFixSolution | FeatureDesignSolution | null>(null)
  const [codeBody, setCodeBody] = useState<CodeGenTask | null>(null)
  const [testBody, setTestBody] = useState<TestTask | null>(null)

  useEffect(() => {
    if (reviewId) {
      loadReviewDetail(reviewId)
    }
  }, [reviewId])

  useEffect(() => {
    if (!review) return
    setSolutionBody(null)
    setCodeBody(null)
    setTestBody(null)
    if (review.item_type === 'solution') {
      solutionService.getSolution(review.item_id).then(setSolutionBody).catch(() => setSolutionBody(null))
    } else if (review.item_type === 'code') {
      codegenService.getTaskStatus(review.item_id).then(setCodeBody).catch(() => setCodeBody(null))
    } else {
      testService.getTestTask(review.item_id).then(setTestBody).catch(() => setTestBody(null))
    }
  }, [review])

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
    } catch (error) {
      console.error(error)
      setReview(null)
      setComments([])
      setDecisions([])
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
    } catch (error) {
      console.error(error)
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
    } catch (error) {
      console.error(error)
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
                {review.session_id && (
                  <button
                    type="button"
                    onClick={() => navigate(`/chat/${review.session_id}`)}
                    className="text-primary hover:underline"
                  >
                    回到对话
                  </button>
                )}
              </div>

              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 leading-relaxed">
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {review.item_type === 'solution' && solutionBody?.content
                      ? solutionBody.content
                      : review.description}
                  </ReactMarkdown>
                </div>
              </div>

              {review.item_type === 'solution' && solutionBody && (
                <div className="mt-4 rounded-lg border border-gray-200 p-4 text-sm">
                  {'root_cause' in solutionBody && solutionBody.root_cause && (
                    <div className="markdown-body mb-3 text-gray-700">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{solutionBody.root_cause}</ReactMarkdown>
                    </div>
                  )}
                  <p className="mb-2 text-gray-500">涉及文件</p>
                  <ul className="space-y-1 font-mono text-xs text-gray-700">
                    {(solutionBody.affected_files || []).map((file) => <li key={file}>{file}</li>)}
                    {(solutionBody.affected_files || []).length === 0 && <li>没有记录文件</li>}
                  </ul>
                </div>
              )}
              {review.item_type === 'code' && codeBody && (
                <div className="mt-4 rounded-lg border border-gray-200 p-4 text-sm">
                  <p className="mb-2">语法检查：{codeBody.lint_result ? (codeBody.lint_result.passed ? '通过' : '未通过') : '尚未检查'}</p>
                  <ul className="space-y-1 font-mono text-xs text-gray-700">
                    {codeBody.files.map((file) => <li key={file.path}>{file.action} {file.path}</li>)}
                  </ul>
                  {(codeBody.lint_result?.errors || []).map((error) => (
                    <p key={`${error.file}-${error.line}`} className="mt-2 text-xs text-red-600">{error.file}:{error.line} {error.message}</p>
                  ))}
                </div>
              )}
              {review.item_type === 'test' && testBody && (
                <div className="mt-4 rounded-lg border border-gray-200 p-4 text-sm">
                  <p className="mb-2 text-gray-600">测试结果按质量门禁展示，不额外等待人工审批。</p>
                  <p>通过 {testBody.results.filter((item) => item.status === 'passed').length} / {testBody.results.length || testBody.test_cases.length}，覆盖率 {testBody.coverage}%</p>
                  {testBody.results.filter((item) => item.status === 'failed').map((item) => (
                    <p key={item.test_case_id} className="mt-2 text-xs text-red-600">{item.test_case_id} {item.error_message || '失败'}</p>
                  ))}
                </div>
              )}

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
