interface CoverageBarProps {
  percent: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const sizeConfig = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
}

function getCoverageColor(percent: number): string {
  if (percent >= 80) return 'bg-green-500'
  if (percent >= 60) return 'bg-yellow-500'
  if (percent >= 40) return 'bg-orange-500'
  return 'bg-red-500'
}

function getCoverageTextColor(percent: number): string {
  if (percent >= 80) return 'text-green-600'
  if (percent >= 60) return 'text-yellow-600'
  if (percent >= 40) return 'text-orange-600'
  return 'text-red-600'
}

export default function CoverageBar({ percent, showLabel = true, size = 'md' }: CoverageBarProps) {
  const safePercent = Math.min(100, Math.max(0, percent))
  const colorClass = getCoverageColor(safePercent)
  const textColorClass = getCoverageTextColor(safePercent)

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-gray-600">代码覆盖率</span>
          <span className={`text-sm font-medium ${textColorClass}`}>
            {safePercent.toFixed(1)}%
          </span>
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeConfig[size]}`}>
        <div
          className={`${colorClass} ${sizeConfig[size]} rounded-full transition-all duration-500`}
          style={{ width: `${safePercent}%` }}
        />
      </div>
    </div>
  )
}

export { getCoverageColor, getCoverageTextColor }
