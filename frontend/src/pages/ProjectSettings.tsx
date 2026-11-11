import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AgentCard, AgentConfigModal } from '../components/Agents'
import SkillContentModal from '../components/Skills/SkillContentModal'
import { agentService, projectService } from '../services'
import { projectErrorMessage } from '../services/projectService'
import type { AgentConfig, Project, ProjectMember, ProjectSkill, SandboxSettings, UpdateAgentConfigRequest } from '../types'

const tabs = ['基本信息', 'Agent', 'Skills', 'Sandbox', '成员', '高级'] as const

const emptySandbox = (): SandboxSettings => ({
  backend: 'local',
  memory_mb: 512,
  cpu: 1,
  timeout_seconds: 300,
  network_policy: 'disabled',
  allowed_domains: [],
  run_as_non_root: true,
})

export default function ProjectSettings() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [tab, setTab] = useState<(typeof tabs)[number]>('基本信息')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [prompt, setPrompt] = useState('')
  const [toolchain, setToolchain] = useState('')
  const [skills, setSkills] = useState<ProjectSkill[]>([])
  const [sandbox, setSandbox] = useState<SandboxSettings>(emptySandbox())
  const [domains, setDomains] = useState('')
  const [members, setMembers] = useState<ProjectMember[]>([])
  const [agents, setAgents] = useState<AgentConfig[]>([])
  const [selectedAgent, setSelectedAgent] = useState<AgentConfig | null>(null)
  const [memberName, setMemberName] = useState('')
  const [memberRole, setMemberRole] = useState('developer')
  const [skillName, setSkillName] = useState('')
  const [showSkill, setShowSkill] = useState(false)
  const [viewingSkill, setViewingSkill] = useState<ProjectSkill | null>(null)
  const [message, setMessage] = useState('')
  const [sandboxResult, setSandboxResult] = useState('')
  const [branch, setBranch] = useState('')
  const [sourceFile, setSourceFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importError, setImportError] = useState('')

  useEffect(() => {
    if (!id) return
    projectService.getProject(id).then((data) => {
      setProject(data)
      setName(data.name)
      setDescription(data.description || '')
      setRepoUrl(data.repo_url || '')
      setPrompt(data.prompt_template || '')
      setToolchain(data.toolchain || '')
      setSkills(data.skills || [])
      setSandbox(data.sandbox || emptySandbox())
      setDomains((data.sandbox?.allowed_domains || []).join('\n'))
      setMembers(data.members || [])
    }).catch(() => setProject(null))
    agentService.getAgentConfigs(id).then(setAgents).catch(() => setAgents([]))
  }, [id])

  const handleToggleAgent = async (agent: AgentConfig) => {
    try {
      const updatedAgent = await agentService.toggleAgent(agent.project_id, agent.id, !agent.enabled)
      setAgents((current) => current.map((item) => (item.id === updatedAgent.id ? updatedAgent : item)))
    } catch (error) {
      console.error(error)
    }
  }

  const handleUpdateAgentConfig = async (agentId: string, data: UpdateAgentConfigRequest) => {
    if (!id) return
    const updatedAgent = await agentService.updateAgentConfig(id, agentId, data)
    setAgents((current) => current.map((item) => (item.id === updatedAgent.id ? updatedAgent : item)))
  }

  const save = async (event?: FormEvent) => {
    event?.preventDefault()
    if (!id) return
    const updated = await projectService.updateProject(id, {
      name,
      description,
      repo_url: repoUrl,
      prompt_template: prompt,
      toolchain,
      skills,
      members,
      sandbox: {
        ...sandbox,
        allowed_domains: domains.split('\n').map((item) => item.trim()).filter(Boolean),
      },
    })
    setProject(updated)
    setSkills(updated.skills || [])
    setMessage('已保存')
  }

  const testSandbox = async () => {
    if (!id) return
    await save()
    const result = await projectService.testSandbox(id)
    setSandboxResult(result.message)
  }

  const applyCodeProject = (updated: Project) => {
    setProject(updated)
    setRepoUrl(updated.repo_url || '')
    setMessage(updated.code_message || '源代码已更新')
    setImportError('')
  }

  const syncGit = async () => {
    if (!id || !repoUrl.trim()) {
      setImportError('请先填写仓库地址')
      return
    }
    setImporting(true)
    setImportError('')
    try {
      applyCodeProject(await projectService.importGit(id, repoUrl.trim(), branch.trim()))
    } catch (error) {
      setImportError(projectErrorMessage(error, '从 GitHub 同步失败'))
    } finally {
      setImporting(false)
    }
  }

  const uploadZip = async () => {
    if (!id || !sourceFile) {
      setImportError('请选择 zip 压缩包')
      return
    }
    setImporting(true)
    setImportError('')
    try {
      applyCodeProject(await projectService.uploadSource(id, sourceFile))
      setSourceFile(null)
    } catch (error) {
      setImportError(projectErrorMessage(error, '上传源代码失败'))
    } finally {
      setImporting(false)
    }
  }

  if (!project) {
    return <div className="p-6 text-sm text-gray-500">项目设置加载中...</div>
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-6xl mx-auto">
        <button type="button" onClick={() => navigate(`/projects/${id}`)} className="mb-4 text-sm text-gray-600">← 返回项目</button>
        <h1 className="text-2xl font-semibold text-gray-800 mb-4">项目设置</h1>
        <div className="mb-4 flex flex-wrap gap-2">
          {tabs.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setTab(item)
                if (item === 'Skills' && id) {
                  projectService.getProject(id).then((data) => setSkills(data.skills || [])).catch(() => undefined)
                }
              }}
              className={`rounded-lg px-3 py-1.5 text-sm ${tab === item ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-gray-600'}`}
            >
              {item}
            </button>
          ))}
        </div>
        {tab === 'Agent' && (
          <div className="mb-4">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Agent 配置</h2>
              <p className="text-sm text-gray-500">
                已启用 {agents.filter((agent) => agent.enabled).length}/{agents.length} 个 Agent，与项目详情页使用同一份配置
              </p>
            </div>
            {agents.length === 0 ? (
              <p className="rounded-xl border border-gray-200 bg-white p-5 text-sm text-gray-400">还没有 Agent 配置</p>
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onToggle={handleToggleAgent}
                    onConfigure={setSelectedAgent}
                  />
                ))}
              </div>
            )}
          </div>
        )}
        <form onSubmit={save} className="rounded-xl border border-gray-200 bg-white p-5 space-y-4">
          {tab === '基本信息' && (
            <>
              <label className="block text-sm text-gray-600">名称
                <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
              </label>
              <label className="block text-sm text-gray-600">描述
                <textarea value={description} onChange={(event) => setDescription(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" rows={3} />
              </label>
              <label className="block text-sm text-gray-600">仓库地址
                <input value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/your-org/your-repo" className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
              </label>
              <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 space-y-3">
                <div className="text-sm text-gray-700">
                  代码来源：{project.code_status === 'ready' ? '已导入' : '未导入'}
                  {project.code_origin === 'git' && ' · GitHub'}
                  {project.code_origin === 'upload' && ' · 本地上传'}
                  {project.code_branch ? ` · ${project.code_branch}` : ''}
                  {project.code_revision ? ` · ${project.code_revision.slice(0, 12)}` : ''}
                </div>
                <p className="text-xs text-gray-500">
                  方案生成、代码定位和写回只使用服务器上已上传的这份源代码，不会修改运行服务的工作目录。
                </p>
                <p className="text-xs text-gray-500">
                  {project.code_message || '还没有导入源代码。'}
                  {project.code_updated_at ? ` 更新于 ${new Date(project.code_updated_at).toLocaleString('zh-CN')}` : ''}
                </p>
                <label className="block text-sm text-gray-600">分支
                  <input value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="留空使用默认分支" className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
                </label>
                <div className="flex flex-wrap gap-2">
                  <button type="button" disabled={importing} onClick={syncGit} className="rounded-lg bg-primary px-3 py-2 text-sm text-white disabled:opacity-50">
                    {importing ? '处理中...' : '从 GitHub 同步'}
                  </button>
                </div>
                <label className="block text-sm text-gray-600">上传 zip
                  <input type="file" accept=".zip,application/zip" onChange={(event) => setSourceFile(event.target.files?.[0] || null)} className="mt-1 block w-full text-sm" />
                </label>
                <button type="button" disabled={importing} onClick={uploadZip} className="rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-700 disabled:opacity-50">
                  上传源代码
                </button>
                {importError && <p className="text-sm text-red-600">{importError}</p>}
              </div>
            </>
          )}
          {tab === 'Agent' && (
            <>
              <h2 className="text-sm font-semibold text-gray-800">项目级 Prompt 与工具链</h2>
              <label className="block text-sm text-gray-600">Prompt 模板
                <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 font-mono text-sm" rows={6} />
              </label>
              <label className="block text-sm text-gray-600">工具链
                <textarea value={toolchain} onChange={(event) => setToolchain(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" rows={4} placeholder="例如：检索、代码生成、语法检查、测试执行" />
              </label>
            </>
          )}
          {tab === 'Skills' && (
            <>
              {skills.map((skill) => (
                <div key={skill.key} className="flex items-center justify-between gap-3 rounded-lg border border-gray-100 px-3 py-2 text-sm">
                  <label className="flex min-w-0 flex-1 items-center gap-2">
                    <input
                      type="checkbox"
                      checked={skill.enabled}
                      onChange={(event) => setSkills((current) => current.map((item) => item.key === skill.key ? { ...item, enabled: event.target.checked } : item))}
                    />
                    <span className="min-w-0">
                      {skill.name}
                      {skill.agent && <span className="ml-2 text-xs text-gray-400">{skill.agent}</span>}
                      <span className="ml-2 text-xs text-gray-400">使用 {skill.usage_count || 0} 次</span>
                      <span className="mt-0.5 block text-xs text-gray-400">{skill.description}</span>
                    </span>
                  </label>
                  <button type="button" onClick={() => setViewingSkill(skill)} className="shrink-0 rounded-lg bg-gray-100 px-3 py-1.5 text-xs text-gray-700">
                    查看
                  </button>
                </div>
              ))}
              <button type="button" onClick={() => setShowSkill(true)} className="rounded-lg bg-gray-100 px-3 py-2 text-sm">添加技能</button>
            </>
          )}
          {tab === 'Sandbox' && (
            <>
              <label className="block text-sm text-gray-600">后端
                <select value={sandbox.backend} onChange={(event) => setSandbox({ ...sandbox, backend: event.target.value })} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2">
                  <option value="local">local</option>
                  <option value="docker">docker</option>
                  <option value="kubernetes">kubernetes</option>
                  <option value="e2b">e2b</option>
                </select>
              </label>
              <div className="grid grid-cols-3 gap-3">
                <label className="text-sm text-gray-600">内存 MB
                  <input type="number" value={sandbox.memory_mb} onChange={(event) => setSandbox({ ...sandbox, memory_mb: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
                </label>
                <label className="text-sm text-gray-600">CPU
                  <input type="number" value={sandbox.cpu} onChange={(event) => setSandbox({ ...sandbox, cpu: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
                </label>
                <label className="text-sm text-gray-600">超时秒
                  <input type="number" value={sandbox.timeout_seconds} onChange={(event) => setSandbox({ ...sandbox, timeout_seconds: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
                </label>
              </div>
              <label className="block text-sm text-gray-600">网络策略
                <select value={sandbox.network_policy} onChange={(event) => setSandbox({ ...sandbox, network_policy: event.target.value })} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2">
                  <option value="disabled">禁用网络</option>
                  <option value="allowlist">白名单</option>
                  <option value="open">允许所有</option>
                </select>
              </label>
              <label className="block text-sm text-gray-600">允许域名，一行一个
                <textarea value={domains} onChange={(event) => setDomains(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" rows={3} />
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={sandbox.run_as_non_root}
                  onChange={(event) => setSandbox({ ...sandbox, run_as_non_root: event.target.checked })}
                />
                非 root 运行
              </label>
              <button type="button" onClick={testSandbox} className="rounded-lg bg-gray-800 px-3 py-2 text-sm text-white">连通性测试</button>
              {sandboxResult && <p className="text-sm text-gray-600">{sandboxResult}</p>}
            </>
          )}
          {tab === '成员' && (
            <>
              <div className="flex gap-2">
                <input value={memberName} onChange={(event) => setMemberName(event.target.value)} placeholder="用户名" className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                <select value={memberRole} onChange={(event) => setMemberRole(event.target.value)} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
                  <option value="developer">开发</option>
                  <option value="reviewer">审核</option>
                  <option value="viewer">只读</option>
                </select>
                <button
                  type="button"
                  onClick={() => {
                    if (!memberName.trim()) return
                    setMembers((current) => [...current.filter((item) => item.username !== memberName.trim()), { username: memberName.trim(), role: memberRole }])
                    setMemberName('')
                  }}
                  className="rounded-lg bg-gray-100 px-3 py-2 text-sm"
                >
                  添加
                </button>
              </div>
              {members.map((member) => (
                <div key={member.username} className="flex items-center justify-between text-sm">
                  <span>{member.username} · {member.role}</span>
                  <button type="button" onClick={() => setMembers((current) => current.filter((item) => item.username !== member.username))} className="text-red-600">移除</button>
                </div>
              ))}
              {members.length === 0 && <p className="text-sm text-gray-400">还没有成员</p>}
            </>
          )}
          {tab === '高级' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-600">当前状态：{project.status}</p>
              <button
                type="button"
                onClick={async () => {
                  if (!id) return
                  const updated = await projectService.updateProject(id, { status: project.status === 'archived' ? 'active' : 'archived' })
                  setProject(updated)
                  setMessage(updated.status === 'archived' ? '项目已归档' : '项目已恢复')
                }}
                className="rounded-lg bg-amber-100 px-3 py-2 text-sm text-amber-800"
              >
                {project.status === 'archived' ? '取消归档' : '归档项目'}
              </button>
            </div>
          )}
          {tab !== '高级' && (
            <button type="submit" className="rounded-lg bg-primary px-4 py-2 text-sm text-white">保存</button>
          )}
          {message && <p className="text-sm text-green-600">{message}</p>}
        </form>
        <AgentConfigModal
          isOpen={selectedAgent !== null}
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          onSubmit={handleUpdateAgentConfig}
        />
        <SkillContentModal skill={viewingSkill} onClose={() => setViewingSkill(null)} />
        {showSkill && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-sm rounded-xl bg-white p-5">
              <h2 className="mb-3 font-semibold">添加技能</h2>
              <input value={skillName} onChange={(event) => setSkillName(event.target.value)} className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm" placeholder="技能名称" />
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (!skillName.trim()) return
                    setSkills((current) => [...current, { key: skillName.trim().toLowerCase().replace(/\s+/g, '-'), name: skillName.trim(), description: '自定义技能', enabled: true, usage_count: 0 }])
                    setSkillName('')
                    setShowSkill(false)
                  }}
                  className="rounded-lg bg-primary px-3 py-2 text-sm text-white"
                >
                  确认
                </button>
                <button type="button" onClick={() => setShowSkill(false)} className="rounded-lg bg-gray-100 px-3 py-2 text-sm">取消</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
