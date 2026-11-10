import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AgentCard, AgentConfigModal } from '../components/Agents'
import type { Project, AgentConfig, UpdateAgentConfigRequest } from '../types'
import { projectService, agentService } from '../services'

const mockProject: Project = {
  id: '1',
  name: '用户服务系统',
  description: '核心用户认证与授权服务，支持 OAuth2.0 和 SSO 登录',
  repo_url: 'https://github.com/company/user-service',
  status: 'active',
  created_at: '2024-01-15T08:00:00Z',
  updated_at: '2024-03-10T14:30:00Z',
}

const mockAgents: AgentConfig[] = [
  {
    id: '1',
    project_id: '1',
    agent_type: 'lead',
    name: 'Lead Agent',
    description: '负责任务分类和调度协调',
    model_name: 'gpt-4o',
    temperature: 0.3,
    max_tokens: 8192,
    skills: ['knowledge_query', 'web_search'],
    enabled: true,
  },
  {
    id: '2',
    project_id: '1',
    agent_type: 'bugfix',
    name: 'Bug Fix Agent',
    description: '分析和修复代码缺陷',
    model_name: 'gpt-4o',
    temperature: 0.2,
    max_tokens: 16384,
    skills: ['code_search', 'code_edit', 'terminal_execute', 'git_operations'],
    enabled: true,
  },
  {
    id: '3',
    project_id: '1',
    agent_type: 'feature',
    name: 'Feature Agent',
    description: '实现新功能需求',
    model_name: 'gpt-4o',
    temperature: 0.5,
    max_tokens: 16384,
    skills: ['code_search', 'code_edit', 'file_read', 'file_write', 'terminal_execute'],
    enabled: true,
  },
  {
    id: '4',
    project_id: '1',
    agent_type: 'doc',
    name: 'Doc Agent',
    description: '生成和更新文档',
    model_name: 'gpt-4o-mini',
    temperature: 0.7,
    max_tokens: 8192,
    skills: ['code_search', 'file_read', 'file_write'],
    enabled: false,
  },
  {
    id: '5',
    project_id: '1',
    agent_type: 'review',
    name: 'Review Agent',
    description: '代码审查和质量检测',
    model_name: 'gpt-4o',
    temperature: 0.1,
    max_tokens: 16384,
    skills: ['code_search', 'lint_check', 'test_runner'],
    enabled: true,
  },
]

const statusConfig = {
  active: { label: '运行中', className: 'bg-green-100 text-green-600' },
  inactive: { label: '已暂停', className: 'bg-amber-100 text-amber-600' },
  archived: { label: '已归档', className: 'bg-gray-100 text-gray-600' },
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [agents, setAgents] = useState<AgentConfig[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState<AgentConfig | null>(null)
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false)

  useEffect(() => {
    if (id) {
      loadProjectData(id)
    }
  }, [id])

  const loadProjectData = async (projectId: string) => {
    setIsLoading(true)
    try {
      const [projectData, agentsData] = await Promise.all([
        projectService.getProject(projectId),
        agentService.getAgentConfigs(projectId),
      ])
      setProject(projectData)
      setAgents(agentsData)
    } catch {
      console.log('Using mock data for development')
      setProject(mockProject)
      setAgents(mockAgents)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleAgent = async (agent: AgentConfig) => {
    try {
      const updatedAgent = await agentService.toggleAgent(
        agent.project_id,
        agent.id,
        !agent.enabled
      )
      setAgents((prev) =>
        prev.map((a) => (a.id === updatedAgent.id ? updatedAgent : a))
      )
    } catch {
      setAgents((prev) =>
        prev.map((a) =>
          a.id === agent.id ? { ...a, enabled: !a.enabled } : a
        )
      )
    }
  }

  const handleConfigureAgent = (agent: AgentConfig) => {
    setSelectedAgent(agent)
    setIsConfigModalOpen(true)
  }

  const handleUpdateAgentConfig = async (
    agentId: string,
    data: UpdateAgentConfigRequest
  ) => {
    if (!id) return
    try {
      const updatedAgent = await agentService.updateAgentConfig(id, agentId, data)
      setAgents((prev) =>
        prev.map((a) => (a.id === updatedAgent.id ? updatedAgent : a))
      )
    } catch {
      setAgents((prev) =>
        prev.map((a) =>
          a.id === agentId ? { ...a, ...data } : a
        )
      )
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">项目不存在</h3>
          <p className="text-gray-500 mb-6">找不到该项目，请检查链接是否正确</p>
          <button
            onClick={() => navigate('/projects')}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors"
          >
            返回项目列表
          </button>
        </div>
      </div>
    )
  }

  const status = statusConfig[project.status]
  const enabledAgentCount = agents.filter((a) => a.enabled).length

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate('/projects')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回项目列表
        </button>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-primary-light rounded-xl flex items-center justify-center text-3xl">
                📁
              </div>
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-2xl font-semibold text-gray-800">
                    {project.name}
                  </h1>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                  >
                    {status.label}
                  </span>
                </div>
                <p className="text-gray-500 mb-3 max-w-2xl">
                  {project.description || '暂无描述'}
                </p>
                <div className="flex items-center gap-6 text-sm text-gray-400">
                  {project.repo_url && (
                    <a
                      href={project.repo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 hover:text-primary transition-colors"
                    >
                      <span>🔗</span>
                      {project.repo_url}
                    </a>
                  )}
                  <span>
                    创建于 {new Date(project.created_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>
              </div>
            </div>
            <button className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              ⚙️ 项目设置
            </button>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">Agent 配置</h2>
              <p className="text-sm text-gray-500">
                已启用 {enabledAgentCount}/{agents.length} 个 Agent
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">批量操作：</span>
              <button
                onClick={() => {
                  agents.forEach((agent) => {
                    if (!agent.enabled) handleToggleAgent(agent)
                  })
                }}
                className="px-3 py-1.5 text-xs font-medium text-primary bg-primary-light hover:bg-primary/20 rounded-lg transition-colors"
              >
                全部启用
              </button>
              <button
                onClick={() => {
                  agents.forEach((agent) => {
                    if (agent.enabled) handleToggleAgent(agent)
                  })
                }}
                className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                全部禁用
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {agents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onToggle={handleToggleAgent}
                onConfigure={handleConfigureAgent}
              />
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>📊</span>
              项目统计
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">128</div>
                <div className="text-sm text-gray-500">总会话数</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">45</div>
                <div className="text-sm text-gray-500">Bug 已修复</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">23</div>
                <div className="text-sm text-gray-500">需求已实现</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">92%</div>
                <div className="text-sm text-gray-500">任务成功率</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>📚</span>
              知识库状态
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-sm text-gray-700">代码库索引</span>
                </div>
                <span className="text-sm text-gray-500">12,345 文件</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-sm text-gray-700">文档库</span>
                </div>
                <span className="text-sm text-gray-500">89 文档</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                  <span className="text-sm text-gray-700">历史会话</span>
                </div>
                <span className="text-sm text-gray-500">同步中...</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <AgentConfigModal
        isOpen={isConfigModalOpen}
        agent={selectedAgent}
        onClose={() => {
          setIsConfigModalOpen(false)
          setSelectedAgent(null)
        }}
        onSubmit={handleUpdateAgentConfig}
      />
    </div>
  )
}
