import type { CodeGenStatus } from '../../types'

interface CodeGenProgressProps {
  status: CodeGenStatus
  className?: string
}

const stages: { key: CodeGenStatus; label: string }[] = [
  { key: 'pending', label: '等待' },
  { key: 'generating', label: '生成代码' },
  { key: 'linting', label: '代码检查' },
  { key: 'completed', label: '完成' },
]

const statusOrder: Record<CodeGenStatus, number> = {
  pending: 0,
  generating: 1,
  linting: 2,
  completed: 3,
  failed: -1,
}

export default function CodeGenProgress({ status, className = '' }: CodeGenProgressProps) {
  const currentOrder = statusOrder[status]
  const isFailed = status === 'failed'

  const getStageStatus = (stageKey: CodeGenStatus) => {
    const stageOrder = statusOrder[stageKey]
    if (isFailed) return 'error'
    if (stageOrder < currentOrder) return 'completed'
    if (stageOrder === currentOrder) return 'active'
    return 'pending'
  }

  const progressPercentage = isFailed ? 0 : Math.min(((currentOrder + 1) / stages.length) * 100, 100)

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-800 mb-4">生成进度</h3>
      
      {isFailed ? (
        <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg border border-red-100">
          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600">
            ✕
          </div>
          <div>
            <p className="font-medium text-red-800">生成失败</p>
            <p className="text-sm text-red-600">请查看错误信息并尝试重新生成</p>
          </div>
        </div>
      ) : (
        <>
          <div className="relative mb-6">
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-500"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          <div className="flex justify-between">
            {stages.map((stage, index) => {
              const stageStatus = getStageStatus(stage.key)
              return (
                <div key={stage.key} className="flex flex-col items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                      stageStatus === 'completed'
                        ? 'bg-green-500 text-white'
                        : stageStatus === 'active'
                        ? 'bg-blue-500 text-white animate-pulse'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    {stageStatus === 'completed' ? '✓' : index + 1}
                  </div>
                  <span
                    className={`mt-2 text-xs font-medium ${
                      stageStatus === 'active'
                        ? 'text-blue-600'
                        : stageStatus === 'completed'
                        ? 'text-green-600'
                        : 'text-gray-400'
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
