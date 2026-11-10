import type { TrendData } from '../../types'

interface TrendChartProps {
  data: TrendData[]
  title: string
  height?: number
}

export default function TrendChart({ data, title, height = 200 }: TrendChartProps) {
  const createdData = data.filter(d => d.type === 'created')
  const completedData = data.filter(d => d.type === 'completed')
  
  const allCounts = data.map(d => d.count)
  const maxValue = Math.max(...allCounts, 1)
  const minValue = Math.min(...allCounts)
  
  const getY = (count: number) => {
    const range = maxValue - minValue || 1
    return height - 40 - ((count - minValue) / range) * (height - 60)
  }
  
  const generatePath = (points: TrendData[]) => {
    if (points.length === 0) return ''
    const width = 100 / (points.length - 1 || 1)
    return points.map((point, i) => {
      const x = i * width
      const y = getY(point.count)
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    }).join(' ')
  }

  const createdPath = generatePath(createdData)
  const completedPath = generatePath(completedData)
  
  const dates = createdData.map(d => d.date.slice(5))

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-800">{title}</h3>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-blue-500 rounded"></span>
            <span className="text-gray-500">新建</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-green-500 rounded"></span>
            <span className="text-gray-500">完成</span>
          </div>
        </div>
      </div>
      
      <div className="relative" style={{ height: `${height}px` }}>
        <svg 
          className="w-full h-full" 
          viewBox={`0 0 100 ${height}`} 
          preserveAspectRatio="none"
        >
          {[0, 25, 50, 75, 100].map(percent => {
            const y = height - 40 - (percent / 100) * (height - 60)
            return (
              <g key={percent}>
                <line
                  x1="0"
                  y1={y}
                  x2="100"
                  y2={y}
                  stroke="#e5e7eb"
                  strokeWidth="0.2"
                />
                <text
                  x="-2"
                  y={y + 1}
                  className="text-[3px] fill-gray-400"
                  textAnchor="end"
                >
                  {Math.round(minValue + (percent / 100) * (maxValue - minValue))}
                </text>
              </g>
            )
          })}
          
          <path
            d={createdPath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="0.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          <path
            d={completedPath}
            fill="none"
            stroke="#22c55e"
            strokeWidth="0.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {createdData.map((point, i) => {
            const x = i * (100 / (createdData.length - 1 || 1))
            const y = getY(point.count)
            return (
              <circle
                key={`created-${i}`}
                cx={x}
                cy={y}
                r="1.2"
                fill="#3b82f6"
                className="hover:r-2 transition-all"
              />
            )
          })}
          
          {completedData.map((point, i) => {
            const x = i * (100 / (completedData.length - 1 || 1))
            const y = getY(point.count)
            return (
              <circle
                key={`completed-${i}`}
                cx={x}
                cy={y}
                r="1.2"
                fill="#22c55e"
                className="hover:r-2 transition-all"
              />
            )
          })}
        </svg>
        
        <div className="absolute bottom-0 left-0 right-0 flex justify-between px-1">
          {dates.map((date, i) => (
            <span key={i} className="text-[10px] text-gray-400">{date}</span>
          ))}
        </div>
      </div>
    </div>
  )
}
