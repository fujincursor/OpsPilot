import { useState, type MouseEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ReviewItem, ReviewItemType } from '../../types'
import { reviewService } from '../../services'
import ReviewStatusBadge from './ReviewStatusBadge'
import { PriorityBadge } from '../Requirements'

interface ReviewCardProps {
  review: ReviewItem
}

const typeConfig: Record<ReviewItemType, { icon: string; label: string }> = {
  solution: { icon: '📋', label: '方案' },
  code: { icon: '💻', label: '代码' },
  test: { icon: '🧪', label: '测试' },
}

function isOverdue(dueAt?: string): boolean {
  if (!dueAt) return false
  return new Date(dueAt) < new Date()
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleDateString('zh-CN')
}

export default function ReviewCard({ review }: ReviewCardProps) {
  const navigate = useNavigate()
  const typeInfo = typeConfig[review.item_type]
  const overdue = isOverdue(review.due_at)
  const canDownload = review.item_type === 'code' && review.status === 'approved'
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState('')

  const downloadCode = async (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    setDownloading(true)
    setDownloadError('')
    try {
      await reviewService.downloadApprovedCode(review.id)
    } catch (error) {
      setDownloadError(error instanceof Error ? error.message : '下载失败')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div
      onClick={() => navigate(`/reviews/${review.id}`)}
      className={`bg-white rounded-xl border p-4 cursor-pointer transition-all hover:shadow-md ${
        overdue ? 'border-red-300 ring-1 ring-red-200' : 'border-gray-200 hover:border-primary/30'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{typeInfo.icon}</span>
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
            {typeInfo.label}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <PriorityBadge priority={review.priority} size="sm" />
          <ReviewStatusBadge status={review.status} size="sm" />
        </div>
      </div>

      <h3 className="mt-3 text-sm font-semibold text-gray-800 line-clamp-2">
        {review.title}
      </h3>

      <p className="mt-2 text-xs text-gray-500 line-clamp-2">
        {review.description}
      </p>

      {canDownload && (
        <div className="mt-3">
          <button
            type="button"
            onClick={downloadCode}
            disabled={downloading}
            className="rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-60"
          >
            {downloading ? '打包中...' : '下载代码'}
          </button>
          {downloadError && <p className="mt-1 text-xs text-red-600">{downloadError}</p>}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center gap-3">
          <span>💬 {review.comments_count}</span>
          {review.reviewer && <span>👤 {review.reviewer}</span>}
        </div>
        <div className="flex items-center gap-2">
          {overdue && (
            <span className="text-red-500 font-medium">⚠️ 已超时</span>
          )}
          <span>{formatDate(review.created_at)}</span>
        </div>
      </div>
    </div>
  )
}
