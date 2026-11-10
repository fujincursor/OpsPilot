import type { LintResult, LintMessage } from '../../types'

interface LintResultCardProps {
  result: LintResult | null
  isLoading?: boolean
  className?: string
}

function LintMessageItem({ message, type }: { message: LintMessage; type: 'error' | 'warning' }) {
  const config = {
    error: {
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-700',
      iconColor: 'text-red-500',
      icon: '✕',
    },
    warning: {
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      textColor: 'text-amber-700',
      iconColor: 'text-amber-500',
      icon: '⚠',
    },
  }[type]

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border ${config.bgColor} ${config.borderColor}`}
    >
      <span className={`${config.iconColor} text-sm mt-0.5`}>{config.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
          <span className="font-mono truncate">{message.file}</span>
          <span>·</span>
          <span>
            行 {message.line}:{message.column}
          </span>
          {message.rule && (
            <>
              <span>·</span>
              <span className="text-gray-400">{message.rule}</span>
            </>
          )}
        </div>
        <p className={`text-sm ${config.textColor}`}>{message.message}</p>
      </div>
    </div>
  )
}

export default function LintResultCard({ result, isLoading, className = '' }: LintResultCardProps) {
  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <div>
            <h3 className="text-sm font-semibold text-gray-800">代码检查中...</h3>
            <p className="text-xs text-gray-500 mt-0.5">正在运行 ESLint / TypeScript 检查</p>
          </div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-400">
          <div className="text-3xl mb-2">🔍</div>
          <p className="text-sm">暂无检查结果</p>
        </div>
      </div>
    )
  }

  const errorCount = result.errors.length
  const warningCount = result.warnings.length
  const hasIssues = errorCount > 0 || warningCount > 0

  return (
    <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden ${className}`}>
      <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
          <span>🔍</span>
          代码检查结果
        </h3>
        <div className="flex items-center gap-3">
          {result.passed ? (
            <span className="flex items-center gap-1.5 text-green-600 text-sm font-medium">
              <span className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center text-xs">
                ✓
              </span>
              检查通过
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-red-600 text-sm font-medium">
              <span className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center text-xs">
                ✕
              </span>
              检查未通过
            </span>
          )}
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-center gap-4 mb-4">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
              errorCount > 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'
            }`}
          >
            <span className="text-sm font-bold">{errorCount}</span>
            <span className="text-xs">错误</span>
          </div>
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
              warningCount > 0 ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'
            }`}
          >
            <span className="text-sm font-bold">{warningCount}</span>
            <span className="text-xs">警告</span>
          </div>
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
              result.passed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
            }`}
          >
            <span className="text-sm font-bold">{result.passed ? '✓' : '✕'}</span>
            <span className="text-xs">{result.passed ? '通过' : '失败'}</span>
          </div>
        </div>

        {hasIssues ? (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {result.errors.map((error, index) => (
              <LintMessageItem key={`error-${index}`} message={error} type="error" />
            ))}
            {result.warnings.map((warning, index) => (
              <LintMessageItem key={`warning-${index}`} message={warning} type="warning" />
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center py-8 bg-green-50 rounded-lg">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-green-500 text-2xl mx-auto mb-2">
                ✓
              </div>
              <p className="text-green-700 font-medium">太棒了！代码检查全部通过</p>
              <p className="text-green-600 text-sm mt-1">没有发现任何问题</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
