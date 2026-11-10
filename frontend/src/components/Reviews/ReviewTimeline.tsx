import type { ReviewDecision } from '../../types'

interface ReviewTimelineProps {
  decisions: ReviewDecision[]
  createdAt: string
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

const decisionConfig = {
  approved: {
    icon: '✓',
    label: '通过',
    className: 'bg-green-500 text-white',
    textClass: 'text-green-600',
  },
  rejected: {
    icon: '✕',
    label: '拒绝',
    className: 'bg-red-500 text-white',
    textClass: 'text-red-600',
  },
  revision_requested: {
    icon: '↻',
    label: '要求修改',
    className: 'bg-orange-500 text-white',
    textClass: 'text-orange-600',
  },
}

export default function ReviewTimeline({ decisions, createdAt }: ReviewTimelineProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-800 mb-4 flex items-center gap-2">
        📜 审核历史
      </h3>

      <div className="relative">
        <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-gray-200" />

        <div className="space-y-4">
          {decisions.map((decision, index) => {
            const config = decisionConfig[decision.decision]
            return (
              <div key={decision.id} className="relative flex gap-4">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 ${config.className}`}
                >
                  {config.icon}
                </div>
                <div className="flex-1 pt-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-sm font-semibold ${config.textClass}`}>
                      {config.label}
                    </span>
                    <span className="text-xs text-gray-400">
                      by {decision.reviewer}
                    </span>
                    <span className="text-xs text-gray-400">
                      · {formatDate(decision.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
                    {decision.reason}
                  </p>
                </div>
              </div>
            )
          })}

          <div className="relative flex gap-4">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm bg-gray-200 text-gray-600 z-10">
              📝
            </div>
            <div className="flex-1 pt-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-600">
                  创建审核
                </span>
                <span className="text-xs text-gray-400">
                  · {formatDate(createdAt)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
