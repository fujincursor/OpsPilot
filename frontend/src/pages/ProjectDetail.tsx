import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AgentCard, AgentConfigModal } from '../components/Agents'
import SkillContentModal from '../components/Skills/SkillContentModal'
import type { Project, AgentConfig, KnowledgeBase, UpdateAgentConfigRequest, ProjectSkill, SandboxSettings } from '../types'
import { projectService, agentService, knowledgeService, requirementService } from '../services'
import type { RequirementStatistics } from '../services/requirementService'

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
  const [statistics, setStatistics] = useState<RequirementStatistics | null>(null)
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [skills, setSkills] = useState<ProjectSkill[]>([])
  const [sandbox, setSandbox] = useState<SandboxSettings | null>(null)
  const [configMessage, setConfigMessage] = useState('')
  const [viewingSkill, setViewingSkill] = useState<ProjectSkill | null>(null)

  useEffect(() => {
    if (id) {
      loadProjectData(id)
    }
  }, [id])

  const loadProjectData = async (projectId: string) => {
    setIsLoading(true)
    try {
      const [projectData, agentsData, statisticsData, knowledgeData] = await Promise.all([
        projectService.getProject(projectId),
        agentService.getAgentConfigs(projectId),
        requirementService.getStatistics(projectId).catch(() => null),
        knowledgeService.getKnowledgeBases(projectId).catch(() => []),
      ])
      setProject(projectData)
      setAgents(agentsData)
      setStatistics(statisticsData)
      setKnowledgeBases(knowledgeData)
      setSkills(projectData.skills || [])
      setSandbox(projectData.sandbox || null)
    } catch (error) {
      console.error(error)
      setProject(null)
      setAgents([])
      setStatistics(null)
      setKnowledgeBases([])
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
    } catch (error) {
      console.error(error)
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
    } catch (error) {
      console.error(error)
    }
  }

  const handleSaveRuntime = async () => {
    if (!id || !sandbox) return
    setConfigMessage('')
    try {
      const updated = await projectService.updateProject(id, { skills, sandbox })
      setProject(updated)
      setSkills(updated.skills || skills)
      setSandbox(updated.sandbox || sandbox)
      setConfigMessage('运行配置已保存')
    } catch {
      setConfigMessage('保存失败')
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
  const completedCount = statistics?.by_status.completed ?? 0
  const inProgressCount = ['analyzing', 'designing', 'reviewing', 'coding', 'testing'].reduce(
    (sum, key) => sum + (statistics?.by_status[key] ?? 0),
    0
  )
  const requirementRows = [
    { key: 'bug', icon: '🐛', label: 'Bug' },
    { key: 'feature', icon: '✨', label: 'Feature' },
    { key: 'question', icon: '❓', label: 'Question' },
  ]
  const knowledgeStatusColor = {
    pending: 'bg-gray-400',
    indexing: 'bg-amber-500',
    ready: 'bg-green-500',
    error: 'bg-red-500',
  }

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
            <div className="flex gap-2">
              <button
                onClick={() => navigate(`/projects/${project.id}/profile`)}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                项目信息
              </button>
              <button
                onClick={() => navigate(`/projects/${project.id}/settings`)}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                ⚙️ 项目设置
              </button>
            </div>
          </div>
        </div>

        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-800">成员</h2>
            <button type="button" onClick={() => navigate(`/projects/${project.id}/settings`)} className="text-sm text-primary">管理成员</button>
          </div>
          {(project.members || []).length === 0 ? (
            <p className="text-sm text-gray-400">还没有项目成员</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {(project.members || []).map((member) => (
                <span key={member.username} className="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-700">
                  {member.username} · {member.role}
                </span>
              ))}
            </div>
          )}
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>📊</span>
              项目统计
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">{statistics?.total ?? 0}</div>
                <div className="text-sm text-gray-500">需求总数</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">{inProgressCount}</div>
                <div className="text-sm text-gray-500">进行中</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">{completedCount}</div>
                <div className="text-sm text-gray-500">已完成</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-semibold text-gray-800">{knowledgeBases.length}</div>
                <div className="text-sm text-gray-500">知识库</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                <span>📋</span>
                需求管理
              </h3>
              <button
                onClick={() => navigate(`/projects/${id}/requirements`)}
                className="text-sm text-primary hover:text-primary-hover font-medium transition-colors"
              >
                查看全部 →
              </button>
            </div>
            <div className="space-y-3">
              {requirementRows.map((row) => (
                <div key={row.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-sm">{row.icon}</span>
                    <span className="text-sm text-gray-700">{row.label}</span>
                  </div>
                  <span className="text-sm text-gray-500">{statistics?.by_type[row.key] ?? 0} 个</span>
                </div>
              ))}
            </div>
            <button
              onClick={() => navigate(`/projects/${id}/requirements`)}
              className="w-full mt-4 py-2.5 text-sm font-medium text-primary bg-primary-light hover:bg-primary/20 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              📋 进入需求管理
            </button>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                <span>📚</span>
                知识库状态
              </h3>
              <button
                onClick={() => navigate(`/projects/${id}/knowledge`)}
                className="text-sm text-primary hover:text-primary-hover font-medium transition-colors"
              >
                管理知识库 →
              </button>
            </div>
            <div className="space-y-3">
              {knowledgeBases.length === 0 ? (
                <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-500">暂无知识库</div>
              ) : (
                knowledgeBases.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${knowledgeStatusColor[item.status]}`}></span>
                      <span className="text-sm text-gray-700 truncate">{item.name}</span>
                    </div>
                    <span className="text-sm text-gray-500 flex-shrink-0">{item.document_count} 篇文档</span>
                  </div>
                ))
              )}
            </div>
            <button
              onClick={() => navigate(`/projects/${id}/knowledge`)}
              className="w-full mt-4 py-2.5 text-sm font-medium text-primary bg-primary-light hover:bg-primary/20 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              📚 进入知识库管理
            </button>
          </div>
        </div>

        <div className="mt-6 bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">运行配置</h2>
              <p className="text-sm text-gray-500">技能开关和沙箱限制会随代码、测试任务一起展示。</p>
            </div>
            <button
              onClick={handleSaveRuntime}
              className="px-3 py-1.5 text-sm font-medium text-white bg-primary rounded-lg"
            >
              保存配置
            </button>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-2">
              {skills.map((skill) => (
                <div key={skill.key} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <label className="flex min-w-0 flex-1 items-start gap-3">
                    <input
                      type="checkbox"
                      checked={skill.enabled}
                      onChange={(event) => {
                        const enabled = event.target.checked
                        setSkills((current) => current.map((item) => (
                          item.key === skill.key ? { ...item, enabled } : item
                        )))
                      }}
                    />
                    <span>
                      <span className="block text-sm font-medium text-gray-800">
                        {skill.name}
                        {skill.agent ? ` · ${skill.agent}` : ''}
                      </span>
                      <span className="block text-xs text-gray-500">{skill.description}</span>
                    </span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setViewingSkill(skill)}
                    className="shrink-0 rounded-lg bg-white px-3 py-1.5 text-xs text-gray-700 border border-gray-200"
                  >
                    查看
                  </button>
                </div>
              ))}
            </div>
            {sandbox && (
              <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="col-span-2">
                  <span className="block text-gray-500 mb-1">环境类型</span>
                  <select
                    value={sandbox.backend}
                    onChange={(event) => setSandbox({ ...sandbox, backend: event.target.value })}
                    className="w-full border border-gray-200 rounded-md px-2 py-1.5"
                  >
                    <option value="local">Local</option>
                    <option value="docker">Docker</option>
                    <option value="kubernetes">Kubernetes</option>
                    <option value="e2b">E2B</option>
                  </select>
                </label>
                <label>
                  <span className="block text-gray-500 mb-1">内存 MB</span>
                  <input
                    type="number"
                    value={sandbox.memory_mb}
                    onChange={(event) => setSandbox({ ...sandbox, memory_mb: Number(event.target.value) })}
                    className="w-full border border-gray-200 rounded-md px-2 py-1.5"
                  />
                </label>
                <label>
                  <span className="block text-gray-500 mb-1">CPU</span>
                  <input
                    type="number"
                    step="0.5"
                    value={sandbox.cpu}
                    onChange={(event) => setSandbox({ ...sandbox, cpu: Number(event.target.value) })}
                    className="w-full border border-gray-200 rounded-md px-2 py-1.5"
                  />
                </label>
                <label>
                  <span className="block text-gray-500 mb-1">超时秒</span>
                  <input
                    type="number"
                    value={sandbox.timeout_seconds}
                    onChange={(event) => setSandbox({ ...sandbox, timeout_seconds: Number(event.target.value) })}
                    className="w-full border border-gray-200 rounded-md px-2 py-1.5"
                  />
                </label>
                <label>
                  <span className="block text-gray-500 mb-1">网络策略</span>
                  <select
                    value={sandbox.network_policy}
                    onChange={(event) => setSandbox({ ...sandbox, network_policy: event.target.value })}
                    className="w-full border border-gray-200 rounded-md px-2 py-1.5"
                  >
                    <option value="disabled">禁用网络</option>
                    <option value="allowlist">白名单</option>
                    <option value="open">允许所有</option>
                  </select>
                </label>
                <label className="col-span-2">
                  <span className="block text-gray-500 mb-1">域名白名单，用逗号分隔</span>
                  <input
                    value={sandbox.allowed_domains.join(',')}
                    onChange={(event) => setSandbox({
                      ...sandbox,
                      allowed_domains: event.target.value.split(',').map((item) => item.trim()).filter(Boolean),
                    })}
                    className="w-full border border-gray-200 rounded-md px-2 py-1.5"
                  />
                </label>
                <label className="col-span-2 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={sandbox.run_as_non_root}
                    onChange={(event) => setSandbox({ ...sandbox, run_as_non_root: event.target.checked })}
                  />
                  非 root 运行
                </label>
              </div>
            )}
          </div>
          {configMessage && <p className="mt-3 text-sm text-gray-500">{configMessage}</p>}
        </div>
      </div>

      <SkillContentModal skill={viewingSkill} onClose={() => setViewingSkill(null)} />
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
