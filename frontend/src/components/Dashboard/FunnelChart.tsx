import type { FunnelData } from '../../types'

interface FunnelChartProps {
  data: FunnelData[]
  title: string
}

const stageColors = [
  'from-blue-400 to-blue-500',
  'from-cyan-400 to-cyan-500',
  'from-teal-400 to-teal-500',
  'from-green-400 to-green-500',
  'from-emerald-400 to-emerald-500',
  'from-lime-400 to-lime-500',
]

export default function FunnelChart({ data, title }: FunnelChartProps) {
  const maxCount = data[0]?.count || 1

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="text-base font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="space-y-2">
        {data.map((item, index) => {
          const widthPercent = (item.count / maxCount) * 100
          const color = stageColors[index % stageColors.length]
          const dropRate = index > 0 
            ? Math.round(((data[index - 1].count - item.count) / data[index - 1].count) * 100) 
            : 0
          
          return (
            <div key={item.stage} className="relative">
              <div 
                className="flex items-center"
                style={{ paddingLeft: `${(100 - widthPercent) / 2}%`, paddingRight: `${(100 - widthPercent) / 2}%` }}
              >
                <div 
                  className={`w-full bg-gradient-to-r ${color} rounded-md py-3 px-4 flex items-center justify-between text-white shadow-sm transition-all duration-300 hover:scale-[1.02]`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{item.stage}</span>
                    {dropRate > 0 && (
                      <span className="text-xs bg-white/20 px-1.5 py-0.5 rounded">
                        -{ dropRate }%
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold">{item.count}</span>
                    <span className="text-xs opacity-80">({item.percentage}%)</span>
                  </div>
                </div>
              </div>
              
              {index < data.length - 1 && (
                <div className="flex justify-center my-1">
                  <div className="w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[8px] border-t-gray-300" />
                </div>
              )}
            </div>
          )
        })}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">整体转化率</span>
          <span className="font-semibold text-green-600">
            {data.length > 0 ? data[data.length - 1].percentage : 0}%
          </span>
        </div>
      </div>
    </div>
  )
}
