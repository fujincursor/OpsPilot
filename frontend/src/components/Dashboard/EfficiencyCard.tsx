import type { EfficiencyMetrics } from '../../types'

interface EfficiencyCardProps {
  data: EfficiencyMetrics
  title: string
}

const stageConfig = [
  { key: 'avg_analysis_time', label: '需求分析', icon: '🔍', color: 'bg-blue-500' },
  { key: 'avg_design_time', label: '方案设计', icon: '📐', color: 'bg-purple-500' },
  { key: 'avg_coding_time', label: '代码生成', icon: '💻', color: 'bg-green-500' },
  { key: 'avg_test_time', label: '测试执行', icon: '🧪', color: 'bg-orange-500' },
] as const

export default function EfficiencyCard({ data, title }: EfficiencyCardProps) {
  const totalTime = data.avg_analysis_time + data.avg_design_time + data.avg_coding_time + data.avg_test_time
  
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-800">{title}</h3>
        <div className="flex items-center gap-1.5 text-sm">
          <span className="text-gray-500">总耗时</span>
          <span className="font-bold text-primary">{totalTime.toFixed(1)}h</span>
        </div>
      </div>
      
      <div className="mb-4">
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden flex">
          {stageConfig.map((stage) => {
            const value = data[stage.key]
            const percent = (value / totalTime) * 100
            return (
              <div
                key={stage.key}
                className={`${stage.color} h-full transition-all duration-500 first:rounded-l-full last:rounded-r-full`}
                style={{ width: `${percent}%` }}
                title={`${stage.label}: ${value}h (${percent.toFixed(0)}%)`}
              />
            )
          })}
        </div>
      </div>
      
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {stageConfig.map((stage) => {
          const value = data[stage.key]
          const percent = (value / totalTime) * 100
          
          return (
            <div 
              key={stage.key} 
              className="text-center p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="text-xl mb-1">{stage.icon}</div>
              <div className="text-lg font-bold text-gray-800">{value}h</div>
              <div className="text-xs text-gray-500">{stage.label}</div>
              <div className="text-[10px] text-gray-400 mt-0.5">{percent.toFixed(0)}%</div>
            </div>
          )
        })}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-2 flex-wrap">
          {stageConfig.map((stage) => (
            <div key={stage.key} className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className={`w-2 h-2 rounded-full ${stage.color}`}></span>
              <span>{stage.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
