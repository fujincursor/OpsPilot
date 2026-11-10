import type { CodeGenStep } from '../../types'

interface SolutionStepsProps {
  steps: CodeGenStep[]
  className?: string
}

const statusLabel: Record<CodeGenStep['status'], string> = {
  pending: '待执行',
  running: '执行中',
  completed: '已完成',
  failed: '失败',
}

export default function SolutionSteps({ steps, className = '' }: SolutionStepsProps) {
  if (steps.length === 0) return null

  const finished = steps.filter((step) => step.status === 'completed').length

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-800">方案步骤</h3>
        <span className="text-xs text-gray-500">
          {finished}/{steps.length} 步已完成
        </span>
      </div>
      <div className="space-y-3">
        {steps.map((step) => (
          <div key={step.index} className="rounded-lg border border-gray-100 p-4">
            <div className="flex items-start gap-3">
              <span
                className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-medium ${
                  step.status === 'completed'
                    ? 'bg-green-500 text-white'
                    : step.status === 'running'
                    ? 'bg-blue-500 text-white'
                    : step.status === 'failed'
                    ? 'bg-red-500 text-white'
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                {step.status === 'completed' ? '✓' : step.status === 'failed' ? '!' : step.index}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-gray-800">{step.title}</p>
                  <span
                    className={`text-xs ${
                      step.status === 'running'
                        ? 'text-blue-600'
                        : step.status === 'completed'
                        ? 'text-green-600'
                        : step.status === 'failed'
                        ? 'text-red-600'
                        : 'text-gray-400'
                    }`}
                  >
                    {statusLabel[step.status]}
                  </span>
                </div>
                {step.status === 'running' && (
                  <p className="mt-2 text-sm text-gray-500">
                    {step.title.includes('定位') ? '正在项目代码中查找位置...' : '正在根据这一步生成结果...'}
                  </p>
                )}
                {step.output && (
                  <p className="mt-2 whitespace-pre-wrap text-sm text-gray-600">{step.output}</p>
                )}
                {(step.locations?.length || 0) > 0 && (
                  <div className="mt-3 space-y-2">
                    {step.locations?.map((location) => (
                      <div key={`${location.path}:${location.line}`} className="rounded-md bg-gray-50 px-3 py-2">
                        <code className="text-xs font-medium text-gray-800">
                          {location.path}:{location.line}
                        </code>
                        <p className="mt-1 text-sm text-gray-600">{location.reason}</p>
                        {location.snippet && (
                          <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-xs text-gray-500">{location.snippet}</pre>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {step.error_message && (
                  <p className="mt-2 text-sm text-red-600">{step.error_message}</p>
                )}
                {(step.files?.length || 0) > 0 && (
                  <p className="mt-2 text-xs text-gray-400">
                    产出文件：{step.files?.map((file) => file.path).join('、')}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
