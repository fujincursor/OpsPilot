import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { BugFixSolution } from '../../types'

interface BugFixViewProps {
  solution: BugFixSolution
}

const riskLevelConfig = {
  low: {
    label: '低风险',
    className: 'bg-green-100 text-green-700 border-green-200',
    icon: '✅',
  },
  medium: {
    label: '中风险',
    className: 'bg-amber-100 text-amber-700 border-amber-200',
    icon: '⚠️',
  },
  high: {
    label: '高风险',
    className: 'bg-red-100 text-red-700 border-red-200',
    icon: '🚨',
  },
}

export default function BugFixView({ solution }: BugFixViewProps) {
  const steps = solution.fix_steps || []
  const risk = solution.regression_risk || { level: 'medium' as const, description: '', affected_areas: [] }
  const riskConfig = riskLevelConfig[risk.level] || riskLevelConfig.medium

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl border border-red-200 overflow-hidden">
        <div className="px-4 py-3 bg-red-100/50 border-b border-red-200">
          <div className="flex items-center gap-2">
            <span>🔍</span>
            <span className="font-semibold text-red-800">根因分析</span>
          </div>
        </div>
        <div className="p-4">
          <div className="markdown-body text-sm text-gray-700">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{solution.root_cause}</ReactMarkdown>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <span>🔧</span>
            <span className="font-semibold text-gray-800">修复步骤</span>
            <span className="px-2 py-0.5 bg-gray-200 rounded-full text-xs text-gray-600">
              {steps.length} 步
            </span>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          {steps.map((step) => (
            <div key={step.order} className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-primary-light rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold text-primary">{step.order}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="markdown-body text-sm text-gray-700 mb-2">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{step.description}</ReactMarkdown>
                  </div>
                  {step.file_path && (
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
                      <span>📄</span>
                      <code className="font-mono">{step.file_path}</code>
                    </div>
                  )}
                  {step.code_snippet && (
                    <pre className="p-3 bg-gray-900 rounded-lg overflow-x-auto">
                      <code className="text-sm text-gray-100 font-mono whitespace-pre">
                        {step.code_snippet}
                      </code>
                    </pre>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={`rounded-xl border overflow-hidden ${riskConfig.className}`}>
        <div className="px-4 py-3 border-b border-current/20">
          <div className="flex items-center gap-2">
            <span>{riskConfig.icon}</span>
            <span className="font-semibold">回归风险评估</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${riskConfig.className}`}>
              {riskConfig.label}
            </span>
          </div>
        </div>
        <div className="p-4 bg-white/50">
          <div className="markdown-body text-sm text-gray-700 mb-3">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{risk.description}</ReactMarkdown>
          </div>
          {(risk.affected_areas || []).length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-2">可能受影响的区域：</div>
              <div className="flex flex-wrap gap-2">
                {risk.affected_areas.map((area, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-white rounded-md text-xs text-gray-600 border border-gray-200"
                  >
                    {area}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
