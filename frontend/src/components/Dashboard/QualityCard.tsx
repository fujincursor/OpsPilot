import type { QualityMetrics } from '../../types'

interface QualityCardProps {
  data: QualityMetrics
  title: string
}

interface MetricItemProps {
  label: string
  value: number
  icon: string
  color: string
  suffix?: string
}

function MetricItem({ label, value, icon, color, suffix = '%' }: MetricItemProps) {
  const getColorClass = (val: number) => {
    if (val >= 90) return 'text-green-600'
    if (val >= 70) return 'text-amber-600'
    return 'text-red-600'
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className={`text-2xl font-bold ${getColorClass(value)}`}>
          {value.toFixed(1)}{suffix}
        </span>
      </div>
      <div className="text-sm text-gray-600">{label}</div>
      <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  )
}

export default function QualityCard({ data, title }: QualityCardProps) {
  const avgScore = (data.first_pass_rate + data.code_quality_score + data.test_coverage_avg) / 3

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-800">{title}</h3>
        <div className="flex items-center gap-1.5 text-sm">
          <span className="text-gray-500">综合评分</span>
          <span className={`font-bold ${avgScore >= 85 ? 'text-green-600' : avgScore >= 70 ? 'text-amber-600' : 'text-red-600'}`}>
            {avgScore.toFixed(1)}
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <MetricItem
          label="一次通过率"
          value={data.first_pass_rate}
          icon="🎯"
          color="bg-blue-500"
        />
        <MetricItem
          label="代码质量"
          value={data.code_quality_score}
          icon="⭐"
          color="bg-purple-500"
        />
        <MetricItem
          label="测试覆盖率"
          value={data.test_coverage_avg}
          icon="🧪"
          color="bg-green-500"
        />
      </div>
    </div>
  )
}
