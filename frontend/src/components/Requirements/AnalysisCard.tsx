import type { AnalysisResult } from '../../types'
import TypeIcon from './TypeIcon'
import PriorityBadge from './PriorityBadge'

interface AnalysisCardProps {
  analysis: AnalysisResult
  isLoading?: boolean
}

export default function AnalysisCard({ analysis, isLoading = false }: AnalysisCardProps) {
  if (isLoading) {
    return (
      <div className="p-4 bg-gradient-to-br from-primary-light to-blue-50 rounded-xl border border-primary/20 animate-pulse">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">🤖</span>
          <span className="font-semibold text-gray-800">AI 分析中...</span>
        </div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-200 rounded w-2/3" />
        </div>
      </div>
    )
  }

  const confidenceColor = 
    analysis.confidence >= 0.8 ? 'text-green-600' :
    analysis.confidence >= 0.5 ? 'text-amber-600' : 'text-red-600'

  const confidenceLabel =
    analysis.confidence >= 0.8 ? '高置信度' :
    analysis.confidence >= 0.5 ? '中置信度' : '低置信度'

  return (
    <div className="p-4 bg-gradient-to-br from-primary-light to-blue-50 rounded-xl border border-primary/20">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">🤖</span>
          <span className="font-semibold text-gray-800">AI 分析结果</span>
        </div>
        <span className={`text-sm font-medium ${confidenceColor}`}>
          {confidenceLabel} ({Math.round(analysis.confidence * 100)}%)
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500 mb-1.5">识别类型</div>
          <TypeIcon type={analysis.type} showLabel size="md" />
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1.5">建议优先级</div>
          <PriorityBadge priority={analysis.priority} size="md" />
        </div>
      </div>

      <div>
        <div className="text-xs text-gray-500 mb-2">关键词提取</div>
        <div className="flex flex-wrap gap-1.5">
          {analysis.keywords.map((keyword, index) => (
            <span
              key={index}
              className="px-2 py-0.5 bg-white rounded-md text-xs text-gray-600 border border-gray-200"
            >
              {keyword}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-primary/10">
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <span>💡</span>
          <span>分析结果仅供参考，请根据实际情况调整</span>
        </div>
      </div>
    </div>
  )
}
