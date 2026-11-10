import { useState, useEffect } from 'react'
import type { AgentConfig, UpdateAgentConfigRequest } from '../../types'

interface AgentConfigModalProps {
  isOpen: boolean
  agent: AgentConfig | null
  onClose: () => void
  onSubmit: (agentId: string, data: UpdateAgentConfigRequest) => Promise<void>
}

const modelOptions = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
  { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
]

const availableSkills = [
  'code_search',
  'code_edit',
  'terminal_execute',
  'web_search',
  'file_read',
  'file_write',
  'knowledge_query',
  'git_operations',
  'test_runner',
  'lint_check',
]

const agentTypeLabels: Record<AgentConfig['agent_type'], string> = {
  lead: 'Lead Agent - 任务分类与调度',
  bugfix: 'Bug Fix Agent - Bug 分析与修复',
  feature: 'Feature Agent - 需求实现',
  doc: 'Doc Agent - 文档生成',
  review: 'Review Agent - 代码审查',
  codegen: 'CodeGen Agent - 代码生成',
  test: 'Test Agent - 测试执行',
}

export default function AgentConfigModal({
  isOpen,
  agent,
  onClose,
  onSubmit,
}: AgentConfigModalProps) {
  const [formData, setFormData] = useState<UpdateAgentConfigRequest>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (agent) {
      setFormData({
        model_name: agent.model_name,
        temperature: agent.temperature,
        max_tokens: agent.max_tokens,
        skills: [...agent.skills],
        enabled: agent.enabled,
      })
    }
  }, [agent])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!agent) return

    setIsSubmitting(true)
    try {
      await onSubmit(agent.id, formData)
      onClose()
    } catch (error) {
      console.error('Failed to update agent config:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSkillToggle = (skill: string) => {
    setFormData((prev) => {
      const currentSkills = prev.skills || []
      const newSkills = currentSkills.includes(skill)
        ? currentSkills.filter((s) => s !== skill)
        : [...currentSkills, skill]
      return { ...prev, skills: newSkills }
    })
  }

  if (!isOpen || !agent) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 overflow-hidden max-h-[90vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-lg font-semibold text-gray-800">配置 Agent</h2>
          <p className="text-sm text-gray-500 mt-1">
            {agentTypeLabels[agent.agent_type] ?? agent.agent_type}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="px-6 py-4 space-y-5 overflow-y-auto flex-1">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                模型选择
              </label>
              <select
                value={formData.model_name || ''}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, model_name: e.target.value }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                {modelOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Temperature: {formData.temperature?.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={formData.temperature || 0}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    temperature: parseFloat(e.target.value),
                  }))
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>精确 (0)</span>
                <span>创意 (2)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Max Tokens
              </label>
              <input
                type="number"
                min="256"
                max="128000"
                step="256"
                value={formData.max_tokens || 4096}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    max_tokens: parseInt(e.target.value, 10),
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
              <p className="text-xs text-gray-400 mt-1">
                控制输出长度，推荐值：4096 - 16384
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                启用技能
              </label>
              <div className="grid grid-cols-2 gap-2">
                {availableSkills.map((skill) => {
                  const isSelected = formData.skills?.includes(skill)
                  return (
                    <button
                      key={skill}
                      type="button"
                      onClick={() => handleSkillToggle(skill)}
                      className={`px-3 py-2 text-sm rounded-lg border transition-colors text-left ${
                        isSelected
                          ? 'bg-primary-light border-primary text-primary font-medium'
                          : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      <span className="mr-1.5">{isSelected ? '✓' : '○'}</span>
                      {skill}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3 justify-end flex-shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? '保存中...' : '保存配置'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
