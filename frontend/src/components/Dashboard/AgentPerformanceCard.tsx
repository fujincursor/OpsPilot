import type { AgentPerformance } from '../../types'

interface AgentPerformanceCardProps {
  data: AgentPerformance[]
  title: string
}

const agentConfig: Record<string, { icon: string; name: string; color: string }> = {
  lead: { icon: '👑', name: 'Lead Agent', color: 'bg-amber-500' },
  bugfix: { icon: '🐛', name: 'Bug 修复', color: 'bg-red-500' },
  feature: { icon: '✨', name: '功能开发', color: 'bg-purple-500' },
  doc: { icon: '📝', name: '文档生成', color: 'bg-blue-500' },
  review: { icon: '✅', name: '代码审查', color: 'bg-green-500' },
}

export default function AgentPerformanceCard({ data, title }: AgentPerformanceCardProps) {
  const maxTasks = Math.max(...data.map(d => d.tasks_completed), 1)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="text-base font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="space-y-4">
        {data.length === 0 ? (
          <p className="text-sm text-gray-400">暂无 Agent 数据</p>
        ) : data.map((agent) => {
          const config = agentConfig[agent.agent_type] || { 
            icon: '🤖', 
            name: agent.agent_type, 
            color: 'bg-gray-500' 
          }
          const barWidth = (agent.tasks_completed / maxTasks) * 100
          
          return (
            <div key={agent.agent_type} className="group">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{config.icon}</span>
                  <span className="text-sm font-medium text-gray-700">{config.name}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                    {agent.success_rate}% 成功率
                  </span>
                  <span>{agent.avg_time}h 平均</span>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${config.color} rounded-full transition-all duration-500 group-hover:opacity-80`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-700 w-12 text-right">
                  {agent.tasks_completed}
                </span>
              </div>
            </div>
          )
        })}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-lg font-bold text-gray-800">
            {data.reduce((sum, a) => sum + a.tasks_completed, 0)}
          </div>
          <div className="text-xs text-gray-500">总任务数</div>
        </div>
        <div>
          <div className="text-lg font-bold text-green-600">
            {(data.reduce((sum, a) => sum + a.success_rate, 0) / data.length).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">平均成功率</div>
        </div>
        <div>
          <div className="text-lg font-bold text-blue-600">
            {(data.reduce((sum, a) => sum + a.avg_time, 0) / data.length).toFixed(1)}h
          </div>
          <div className="text-xs text-gray-500">平均耗时</div>
        </div>
      </div>
    </div>
  )
}
