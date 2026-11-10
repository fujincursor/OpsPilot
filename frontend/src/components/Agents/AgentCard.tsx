import type { AgentConfig } from '../../types'

interface AgentCardProps {
  agent: AgentConfig
  onToggle: (agent: AgentConfig) => void
  onConfigure: (agent: AgentConfig) => void
}

const agentTypeConfig = {
  lead: {
    icon: '🎯',
    label: 'Lead Agent',
    description: '任务分类与调度',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-300',
    iconBg: 'bg-indigo-500',
  },
  bugfix: {
    icon: '🐛',
    label: 'Bug Fix Agent',
    description: 'Bug 分析与修复',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
    iconBg: 'bg-red-500',
  },
  feature: {
    icon: '✨',
    label: 'Feature Agent',
    description: '需求实现',
    bgColor: 'bg-emerald-50',
    borderColor: 'border-emerald-300',
    iconBg: 'bg-emerald-500',
  },
  doc: {
    icon: '📝',
    label: 'Doc Agent',
    description: '文档生成',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-300',
    iconBg: 'bg-amber-500',
  },
  review: {
    icon: '🔍',
    label: 'Review Agent',
    description: '代码审查',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-300',
    iconBg: 'bg-purple-500',
  },
}

export default function AgentCard({ agent, onToggle, onConfigure }: AgentCardProps) {
  const config = agentTypeConfig[agent.agent_type]

  return (
    <div
      className={`rounded-xl p-5 border-2 transition-all ${
        agent.enabled
          ? `${config.bgColor} ${config.borderColor}`
          : 'bg-gray-50 border-gray-200 opacity-60'
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
              agent.enabled ? config.iconBg : 'bg-gray-400'
            } text-white shadow-sm`}
          >
            {config.icon}
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">{agent.name}</h3>
            <p className="text-xs text-gray-500">{config.description}</p>
          </div>
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggle(agent)
          }}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            agent.enabled ? 'bg-primary' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${
              agent.enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">模型</span>
          <span className="font-medium text-gray-700">{agent.model_name}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Temperature</span>
          <span className="font-medium text-gray-700">{agent.temperature}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Max Tokens</span>
          <span className="font-medium text-gray-700">{agent.max_tokens.toLocaleString()}</span>
        </div>
      </div>

      {agent.skills.length > 0 && (
        <div className="mb-4">
          <span className="text-xs text-gray-500 mb-2 block">技能</span>
          <div className="flex flex-wrap gap-1.5">
            {agent.skills.slice(0, 3).map((skill) => (
              <span
                key={skill}
                className="px-2 py-0.5 bg-white/60 rounded text-xs text-gray-600"
              >
                {skill}
              </span>
            ))}
            {agent.skills.length > 3 && (
              <span className="px-2 py-0.5 bg-white/60 rounded text-xs text-gray-500">
                +{agent.skills.length - 3}
              </span>
            )}
          </div>
        </div>
      )}

      <button
        onClick={() => onConfigure(agent)}
        className="w-full py-2 text-sm font-medium text-gray-600 bg-white/80 hover:bg-white rounded-lg border border-gray-200 transition-colors"
      >
        ⚙️ 配置参数
      </button>
    </div>
  )
}
