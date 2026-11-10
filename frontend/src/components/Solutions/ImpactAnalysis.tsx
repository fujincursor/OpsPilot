interface ImpactAnalysisProps {
  analysis: string
}

export default function ImpactAnalysis({ analysis }: ImpactAnalysisProps) {
  const text = typeof analysis === 'string' ? analysis : ''
  const sections = text.split('\n\n').filter(Boolean)

  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 overflow-hidden">
      <div className="px-4 py-3 bg-amber-100/50 border-b border-amber-200">
        <div className="flex items-center gap-2">
          <span>⚡</span>
          <span className="font-semibold text-amber-800">影响分析</span>
        </div>
      </div>
      <div className="p-4">
        {sections.length > 1 ? (
          <div className="space-y-3">
            {sections.map((section, index) => (
              <div key={index} className="p-3 bg-white/60 rounded-lg">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{section}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {text || '暂无影响分析'}
          </p>
        )}
      </div>
    </div>
  )
}
