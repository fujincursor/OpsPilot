import type { TestReport } from '../../types'
import CoverageBar from './CoverageBar'

interface TestReportCardProps {
  report: TestReport
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const seconds = ms / 1000
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

function getPassRateColor(rate: number): { ring: string; text: string; bg: string } {
  if (rate >= 90) return { ring: 'stroke-green-500', text: 'text-green-600', bg: 'bg-green-50' }
  if (rate >= 70) return { ring: 'stroke-yellow-500', text: 'text-yellow-600', bg: 'bg-yellow-50' }
  if (rate >= 50) return { ring: 'stroke-orange-500', text: 'text-orange-600', bg: 'bg-orange-50' }
  return { ring: 'stroke-red-500', text: 'text-red-600', bg: 'bg-red-50' }
}

interface DonutChartProps {
  percent: number
  size?: number
  strokeWidth?: number
}

function DonutChart({ percent, size = 120, strokeWidth = 12 }: DonutChartProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (percent / 100) * circumference
  const colors = getPassRateColor(percent)

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          className={`${colors.ring} transition-all duration-700`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-2xl font-bold ${colors.text}`}>{percent.toFixed(0)}%</span>
        <span className="text-xs text-gray-500">通过率</span>
      </div>
    </div>
  )
}

export default function TestReportCard({ report }: TestReportCardProps) {
  const passRate = report.total > 0 ? (report.passed / report.total) * 100 : 0
  const colors = getPassRateColor(passRate)

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-6 flex items-center gap-2">
        <span>📊</span>
        测试报告
      </h3>

      <div className="flex items-center gap-8">
        <DonutChart percent={passRate} />

        <div className="flex-1 grid grid-cols-2 gap-4">
          <div className={`rounded-lg p-4 ${colors.bg}`}>
            <div className="text-sm text-gray-600 mb-1">测试用例</div>
            <div className="text-2xl font-bold text-gray-800">{report.total}</div>
          </div>

          <div className="rounded-lg p-4 bg-green-50">
            <div className="text-sm text-gray-600 mb-1">通过</div>
            <div className="text-2xl font-bold text-green-600">{report.passed}</div>
          </div>

          <div className="rounded-lg p-4 bg-red-50">
            <div className="text-sm text-gray-600 mb-1">失败</div>
            <div className="text-2xl font-bold text-red-600">{report.failed}</div>
          </div>

          <div className="rounded-lg p-4 bg-gray-50">
            <div className="text-sm text-gray-600 mb-1">跳过</div>
            <div className="text-2xl font-bold text-gray-600">{report.skipped}</div>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-100 space-y-4">
        <CoverageBar percent={report.coverage_percent} size="md" />

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">运行耗时</span>
          <span className="font-medium text-gray-800">{formatDuration(report.duration_ms ?? report.duration ?? 0)}</span>
        </div>
      </div>
    </div>
  )
}

export { DonutChart, formatDuration }
