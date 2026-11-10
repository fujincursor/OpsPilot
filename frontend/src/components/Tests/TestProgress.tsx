import type { TestStatus } from '../../types'

interface TestProgressProps {
  status: TestStatus
  className?: string
}

const steps = [
  { key: 'pending', label: '等待', icon: '⏳' },
  { key: 'generating', label: '生成用例', icon: '📝' },
  { key: 'running', label: '运行测试', icon: '🧪' },
  { key: 'completed', label: '完成', icon: '✅' },
]

const statusIndex: Record<TestStatus, number> = {
  pending: 0,
  generating: 1,
  running: 2,
  completed: 3,
  failed: -1,
}

export default function TestProgress({ status, className = '' }: TestProgressProps) {
  const currentIndex = statusIndex[status]
  const isFailed = status === 'failed'

  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm p-6 ${className}`}>
      <h3 className="text-sm font-medium text-gray-700 mb-4">测试进度</h3>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isActive = index === currentIndex
          const isCompleted = currentIndex > index
          const isCurrent = isActive && !isFailed

          return (
            <div key={step.key} className="flex-1 flex flex-col items-center relative">
              {index > 0 && (
                <div
                  className={`absolute left-0 top-5 w-1/2 h-0.5 -translate-x-1/2 ${
                    isCompleted ? 'bg-green-500' : isFailed && currentIndex === -1 ? 'bg-red-300' : 'bg-gray-200'
                  }`}
                />
              )}
              {index < steps.length - 1 && (
                <div
                  className={`absolute right-0 top-5 w-1/2 h-0.5 translate-x-1/2 ${
                    isCompleted && index < currentIndex ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}

              <div
                className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all ${
                  isFailed && isActive
                    ? 'bg-red-100 border-2 border-red-500'
                    : isCompleted
                    ? 'bg-green-100 border-2 border-green-500'
                    : isCurrent
                    ? 'bg-blue-100 border-2 border-blue-500 animate-pulse'
                    : 'bg-gray-100 border-2 border-gray-300'
                }`}
              >
                {isFailed && isActive ? '❌' : isCompleted ? '✓' : step.icon}
              </div>
              <span
                className={`mt-2 text-xs font-medium ${
                  isFailed && isActive
                    ? 'text-red-600'
                    : isCompleted
                    ? 'text-green-600'
                    : isCurrent
                    ? 'text-blue-600'
                    : 'text-gray-500'
                }`}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
