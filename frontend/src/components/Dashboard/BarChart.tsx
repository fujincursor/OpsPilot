interface BarData {
  label: string
  value: number
  color?: string
}

interface BarChartProps {
  data: BarData[]
  title: string
  maxValue?: number
  showValues?: boolean
  horizontal?: boolean
}

const defaultColors = [
  'bg-blue-500',
  'bg-green-500',
  'bg-purple-500',
  'bg-orange-500',
  'bg-cyan-500',
  'bg-pink-500',
]

export default function BarChart({
  data,
  title,
  maxValue,
  showValues = true,
  horizontal = false,
}: BarChartProps) {
  const max = maxValue || Math.max(...data.map(d => d.value), 1)

  if (horizontal) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <h3 className="text-base font-semibold text-gray-800 mb-4">{title}</h3>
        <div className="space-y-3">
          {data.map((item, index) => {
            const percentage = (item.value / max) * 100
            const color = item.color || defaultColors[index % defaultColors.length]
            return (
              <div key={item.label}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600">{item.label}</span>
                  {showValues && (
                    <span className="font-medium text-gray-800">{item.value}</span>
                  )}
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${color} rounded-full transition-all duration-500`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="text-base font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="flex items-end justify-between gap-2 h-40">
        {data.map((item, index) => {
          const percentage = (item.value / max) * 100
          const color = item.color || defaultColors[index % defaultColors.length]
          return (
            <div key={item.label} className="flex-1 flex flex-col items-center">
              <div className="w-full flex flex-col items-center justify-end h-32">
                {showValues && (
                  <span className="text-xs font-medium text-gray-600 mb-1">
                    {item.value}
                  </span>
                )}
                <div
                  className={`w-full max-w-[40px] ${color} rounded-t-md transition-all duration-500`}
                  style={{ height: `${percentage}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 mt-2 text-center truncate w-full">
                {item.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
