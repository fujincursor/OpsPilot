import type { StatusHistoryItem, RequirementStatus } from '../../types'
import { statusConfig } from './StatusBadge'

interface StatusTimelineProps {
  history: StatusHistoryItem[]
  currentStatus: RequirementStatus
}

export default function StatusTimeline({ history, currentStatus }: StatusTimelineProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const allStatuses: RequirementStatus[] = [
    'pending', 'analyzing', 'designing', 'reviewing', 'coding', 'testing', 'completed'
  ]

  const currentIndex = allStatuses.indexOf(currentStatus)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <span>📋</span>
        状态流转
      </h3>

      <div className="relative">
        <div className="flex items-center justify-between mb-6">
          {allStatuses.map((status, index) => {
            const config = statusConfig[status]
            const isPast = index < currentIndex
            const isCurrent = index === currentIndex

            return (
              <div key={status} className="flex flex-col items-center relative z-10">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 transition-all ${
                    isCurrent
                      ? `${config.className} border-current shadow-md`
                      : isPast
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'bg-gray-100 border-gray-200 text-gray-400'
                  }`}
                >
                  {isPast ? '✓' : index + 1}
                </div>
                <span
                  className={`mt-2 text-[10px] font-medium text-center ${
                    isCurrent ? 'text-gray-800' : isPast ? 'text-green-600' : 'text-gray-400'
                  }`}
                >
                  {config.label}
                </span>
              </div>
            )
          })}
        </div>

        <div className="absolute top-4 left-4 right-4 h-0.5 bg-gray-200 -z-0">
          <div
            className="h-full bg-green-500 transition-all"
            style={{ width: `${(currentIndex / (allStatuses.length - 1)) * 100}%` }}
          />
        </div>
      </div>

      {history.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <h4 className="text-sm font-medium text-gray-700 mb-3">变更历史</h4>
          <div className="space-y-3">
            {history.map((item, index) => {
              const config = statusConfig[item.status]
              return (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div className={`w-2 h-2 rounded-full mt-1.5 ${config.dotColor}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-800">
                        {config.label}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatDate(item.changed_at)}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      由 {item.changed_by} 更新
                    </div>
                    {item.comment && (
                      <div className="mt-1.5 text-xs text-gray-600 bg-white p-2 rounded border border-gray-100">
                        {item.comment}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
