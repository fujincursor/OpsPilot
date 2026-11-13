import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { BugFixSolution, CodeGenTask, CoverageInfo, FeatureDesignSolution, ReviewItem, ReviewComment, ReviewDecision, ReviewItemType, TestReport, TestTask } from '../types'
import { codegenService, reviewService, solutionService, testService } from '../services'
import {
  ReviewStatusBadge,
  ReviewActions,
  CommentSection,
  ReviewTimeline,
  DecisionModal,
} from '../components/Reviews'
import { PriorityBadge } from '../components/Requirements'
import DiffViewer from '../components/CodeGen/DiffViewer'
import { MarkdownBlock } from '../components/Tests/TestResultItem'
import CodeViewer from '../components/CodeGen/CodeViewer'

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

const codeActionLabel: Record<string, string> = {
  create: '新增',
  modify: '修改',
  delete: '删除',
}

function coveragePercent(coverage: TestTask['coverage'], report?: TestReport | null): number {
  if (report && typeof report.coverage_percent === 'number') return report.coverage_percent
  if (typeof coverage === 'number') return coverage
  return coverage?.lines_percent || 0
}

function coverageFiles(coverage: TestTask['coverage'], report?: TestReport | null): CoverageInfo['files'] {
  if (report?.coverage_info?.files) return report.coverage_info.files
  if (coverage && typeof coverage === 'object') return coverage.files
  return undefined
}

function changedFiles(task: CodeGenTask) {
  const changed = task.files.filter((file) => file.action !== 'view')
  return {
    created: changed.filter((file) => file.action === 'create'),
    modified: changed.filter((file) => file.action === 'modify'),
    deleted: changed.filter((file) => file.action === 'delete'),
  }
}

function CodeChanges({
  task,
  selectedPath,
  onSelect,
}: {
  task: CodeGenTask
  selectedPath: string | null
  onSelect: (path: string) => void
}) {
  const groups = changedFiles(task)
  const ordered = [...groups.created, ...groups.modified, ...groups.deleted]
  const selected = ordered.find((file) => file.path === selectedPath) || null

  return (
    <div className="mt-4 rounded-lg border border-gray-200 p-4 text-sm">
      <p className="mb-2">语法检查：{task.lint_result ? (task.lint_result.passed ? '通过' : '未通过') : '尚未检查'}</p>
      <p className="mb-2 text-gray-500">代码变更 · 新增 {groups.created.length} 个，修改 {groups.modified.length} 个，删除 {groups.deleted.length} 个</p>
      {ordered.length === 0 ? (
        <p className="text-xs text-gray-500">没有代码变更</p>
      ) : (
        <div className="space-y-3">
          {([
            ['新增文件', groups.created],
            ['修改的文件', groups.modified],
            ['删除的文件', groups.deleted],
          ] as const).map(([title, files]) => files.length === 0 ? null : (
            <div key={title}>
              <p className="mb-1 text-xs font-medium text-gray-600">{title}</p>
              <ul className="space-y-1">
                {files.map((file) => {
                  const active = file.path === selected?.path
                  return (
                    <li key={file.path}>
                      <button
                        type="button"
                        onClick={() => onSelect(file.path)}
                        className={`w-full rounded-md px-2 py-1.5 text-left font-mono text-xs ${
                          active ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {codeActionLabel[file.action] || file.action} {file.path}
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      )}
      {selected && selected.action !== 'delete' && (
        <div className="mt-3">
          <p className="mb-2 text-xs font-medium text-gray-600">
            {selected.action === 'create' ? '新增的文件' : '变更后的文件'}
          </p>
          <CodeViewer file={selected} />
        </div>
      )}
      {selected && (
        <DiffViewer diff={selected.diff || []} fileName={selected.path} className="mt-3" />
      )}
      {(task.lint_result?.errors || []).map((error) => (
        <p key={`${error.file}-${error.line}`} className="mt-2 text-xs text-red-600">{error.file}:{error.line} {error.message}</p>
      ))}
    </div>
  )
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
  const [notice, setNotice] = useState('')
  const [solutionBody, setSolutionBody] = useState<BugFixSolution | FeatureDesignSolution | null>(null)
  const [codeBody, setCodeBody] = useState<CodeGenTask | null>(null)
  const [testBody, setTestBody] = useState<TestTask | null>(null)
  const [testReport, setTestReport] = useState<TestReport | null>(null)
  const [selectedCodePath, setSelectedCodePath] = useState<string | null>(null)
  const [downloadingCode, setDownloadingCode] = useState(false)

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
    setTestReport(null)
    if (review.item_type === 'solution') {
      solutionService.getSolution(review.item_id).then(setSolutionBody).catch(() => setSolutionBody(null))
    } else if (review.item_type === 'code') {
      codegenService.getTaskStatus(review.item_id).then((task) => {
        setCodeBody(task)
        const { created, modified, deleted } = changedFiles(task)
        const changed = [...created, ...modified, ...deleted]
        setSelectedCodePath((current) =>
          current && changed.some((file) => file.path === current) ? current : changed[0]?.path ?? null
        )
      }).catch(() => setCodeBody(null))
    } else {
      testService.getTestTask(review.item_id).then(setTestBody).catch(() => setTestBody(null))
      testService.getTestReport(review.item_id).then(setTestReport).catch(() => setTestReport(null))
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
      if (modalType === 'approve' && review?.item_type === 'solution') {
        setNotice('已通过。代码生成在后台进行，可到监控查看进度。')
      } else if (modalType === 'approve' && review?.item_type === 'code') {
        setNotice('已通过。测试在后台进行，可到监控查看进度。')
      } else if (modalType === 'revision' && review?.item_type === 'solution') {
        setNotice('已要求修改。方案在后台重新生成，可到监控查看进度。')
      } else if (modalType === 'revision' && review?.item_type === 'code') {
        setNotice('已要求修改。代码在后台重新生成，可到监控查看进度。')
      } else if (modalType === 'reject') {
        setNotice('已拒绝，需求已关闭。')
      } else {
        setNotice('审批结果已提交。')
      }
    } catch (error) {
      console.error(error)
      setNotice('提交没有完成，请稍后重试。')
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
        {notice && (
          <p className={`mb-4 rounded-lg border px-4 py-3 text-sm ${notice.includes('没有完成') ? 'border-red-200 bg-red-50 text-red-700' : 'border-green-200 bg-green-50 text-green-800'}`}>{notice}</p>
        )}

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
              {review.item_type === 'code' && review.status === 'approved' && (
                <button
                  type="button"
                  disabled={downloadingCode}
                  onClick={async () => {
                    setDownloadingCode(true)
                    setNotice('')
                    try {
                      await reviewService.downloadApprovedCode(review.id)
                    } catch (error) {
                      setNotice(error instanceof Error ? error.message : '下载失败')
                    } finally {
                      setDownloadingCode(false)
                    }
                  }}
                  className="mb-6 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
                >
                  {downloadingCode ? '打包中...' : '下载变更代码'}
                </button>
              )}

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
                <CodeChanges
                  task={codeBody}
                  selectedPath={selectedCodePath}
                  onSelect={setSelectedCodePath}
                />
              )}
              {review.item_type === 'test' && testBody && (
                <div className="mt-4 rounded-lg border border-gray-200 p-4 text-sm">
                  <p className="mb-2 text-gray-800">测试已在沙箱中执行修改后的代码。请评审这份报告，通过后需求才完成。</p>
                  {testReport?.summary && (
                    <p className="mb-3 whitespace-pre-wrap text-gray-600">{testReport.summary}</p>
                  )}
                  <p>
                    通过 {testReport?.passed ?? testBody.results.filter((item) => item.status === 'passed').length}
                    {' / '}
                    {testReport?.total ?? (testBody.results.length || testBody.test_cases.length)}
                    ，失败 {testReport?.failed ?? testBody.results.filter((item) => item.status === 'failed').length}
                    ，覆盖率 {coveragePercent(testBody.coverage, testReport).toFixed(0)}%
                  </p>
                  <ul className="mt-3 space-y-2">
                    {testBody.test_cases.map((item) => {
                      const result = testBody.results.find((entry) => entry.test_case_id === item.id)
                      const failed = result?.status === 'failed'
                      return (
                        <li key={item.id} className="rounded-md bg-gray-50 px-3 py-2">
                          <p className={failed ? 'text-red-700' : 'text-gray-800'}>
                            {result?.status === 'passed' ? '通过' : failed ? '失败' : '未执行'} {item.name}
                          </p>
                          {item.description && (
                            <div className="mt-2">
                              <MarkdownBlock text={item.description} />
                            </div>
                          )}
                          {item.target_function && <p className="mt-1 font-mono text-xs text-gray-500">{item.target_function}</p>}
                          {failed && <p className="mt-1 text-xs text-red-600">{result?.error_message || '失败'}</p>}
                        </li>
                      )
                    })}
                  </ul>
                  {Object.entries(coverageFiles(testBody.coverage, testReport) || {}).length > 0 && (
                    <div className="mt-3">
                      <p className="mb-1 text-xs text-gray-500">文件覆盖率</p>
                      <ul className="space-y-1 font-mono text-xs text-gray-700">
                        {Object.entries(coverageFiles(testBody.coverage, testReport) || {}).map(([path, info]) => (
                          <li key={path}>{path} {Number(info.lines_percent || 0).toFixed(0)}%</li>
                        ))}
                      </ul>
                    </div>
                  )}
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
