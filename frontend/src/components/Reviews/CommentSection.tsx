import { useState } from 'react'
import type { ReviewComment } from '../../types'

interface CommentSectionProps {
  comments: ReviewComment[]
  onAddComment: (content: string) => Promise<void>
  isLoading?: boolean
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function CommentSection({
  comments,
  onAddComment,
  isLoading = false,
}: CommentSectionProps) {
  const [newComment, setNewComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!newComment.trim() || isSubmitting) return
    setIsSubmitting(true)
    try {
      await onAddComment(newComment.trim())
      setNewComment('')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit()
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-800 mb-4 flex items-center gap-2">
        💬 评论 ({comments.length})
      </h3>

      {isLoading ? (
        <div className="text-center py-8 text-gray-400">
          <span className="animate-pulse">加载评论中...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {comments.length === 0 ? (
            <div className="text-center py-6 text-gray-400 text-sm">
              暂无评论
            </div>
          ) : (
            comments.map((comment) => (
              <div key={comment.id} className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-medium flex-shrink-0">
                  {comment.author.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-800">
                      {comment.author}
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatDate(comment.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">
                    {comment.content}
                  </p>
                </div>
              </div>
            ))
          )}

          <div className="pt-4 border-t border-gray-100">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="添加评论... (Ctrl+Enter 发送)"
              rows={3}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"
            />
            <div className="mt-2 flex justify-end">
              <button
                onClick={handleSubmit}
                disabled={!newComment.trim() || isSubmitting}
                className="px-4 py-2 bg-primary hover:bg-primary-hover disabled:bg-gray-300 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {isSubmitting ? '发送中...' : '发送评论'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
