import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { AgentConfig, ProjectSkill, Requirement, RequirementStatus, StatusHistoryItem, Solution } from '../types'
import { agentService, projectService, requirementService, solutionService, authService } from '../services'
import { readApiError } from '../services/apiError'
import {
  TypeIcon,
  PriorityBadge,
  StatusBadge,
  AnalysisCard,
  StatusTimeline,
  statusConfig,
} from '../components/Requirements'
import { SolutionCard, GenerateButton } from '../components/Solutions'
import FlowStateBanner from '../components/FlowStateBanner'

export default function RequirementDetail() {
  const { reqId } = useParams<{ reqId: string }>()
  const navigate = useNavigate()
  const [requirement, setRequirement] = useState<Requirement | null>(null)
  const [history, setHistory] = useState<StatusHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [solutions, setSolutions] = useState<Solution[]>([])
  const [teamMembers, setTeamMembers] = useState<string[]>([])
  const [isGeneratingSolution, setIsGeneratingSolution] = useState(false)
  const [isLoadingSolutions, setIsLoadingSolutions] = useState(false)
  const [solutionError, setSolutionError] = useState<string | null>(null)
  const [generateError, setGenerateError] = useState('')
  const [agents, setAgents] = useState<AgentConfig[]>([])
  const [projectSkills, setProjectSkills] = useState<ProjectSkill[]>([])

  useEffect(() => {
    authService.listUsers()
      .then((users) => setTeamMembers(users.map((user) => user.username)))
      .catch(() => setTeamMembers([]))
  }, [])

  useEffect(() => {
    if (!requirement?.project_id) return
    agentService.getAgentConfigs(requirement.project_id)
      .then(setAgents)
      .catch(() => setAgents([]))
    projectService.getProject(requirement.project_id)
      .then((project) => setProjectSkills(project.skills || []))
      .catch(() => setProjectSkills([]))
  }, [requirement?.project_id])

  const solutionActors = (() => {
    if (!requirement || requirement.type === 'question') return null
    const bug = requirement.type === 'bug'
    const skillKey = bug ? 'bugfix-solution' : 'feature-design'
    const agent = agents.find((item) => item.agent_type === (bug ? 'bugfix' : 'feature'))
    const skill = projectSkills.find((item) => item.key === skillKey)
    return {
      agent: agent?.name || (bug ? 'BugFix Agent' : 'Feature Design Agent'),
      skill: skill?.name || (bug ? 'Bug 修复方案' : '功能设计'),
    }
  })()

  useEffect(() => {
    if (reqId) {
      loadRequirement(reqId)
    }
  }, [reqId])

  const loadRequirement = async (id: string) => {
    setIsLoading(true)
    try {
      const req = await requirementService.getRequirement(id)
      setRequirement(req)
      setHistory([
        {
          status: req.status,
          changed_at: req.updated_at || req.created_at,
          changed_by: req.created_by || '',
        },
      ])
    } catch (error) {
      console.error(error)
      setRequirement(null)
      setHistory([])
    } finally {
      setIsLoading(false)
    }
    loadSolutions(id)
  }

  const loadSolutions = async (id: string) => {
    setIsLoadingSolutions(true)
    setSolutionError(null)
    try {
      const data = await solutionService.getSolutions(id)
      setSolutions(data)
    } catch (error) {
      console.error(error)
      setSolutions([])
      setSolutionError('会话记录/解决方案加载失败，请检查网络或稍后重试')
    } finally {
      setIsLoadingSolutions(false)
    }
  }

  const handleGenerateSolution = async () => {
    if (!reqId) return
    setIsGeneratingSolution(true)
    setGenerateError('')
    try {
      const newSolution = await solutionService.generateSolution(reqId)
      const refreshed = await requirementService.getRequirement(reqId)
      setSolutions((prev) => [newSolution, ...prev.filter((item) => item.id !== newSolution.id)])
      setRequirement(refreshed)
      setGenerateError(refreshed.failure_reason || '')
      setSolutionError(null)
    } catch (error) {
      console.error(error)
      const detail = readApiError(error, '方案生成失败')
      setGenerateError(detail)
      setRequirement((current) => current ? { ...current, failure_reason: detail } : current)
    } finally {
      setIsGeneratingSolution(false)
    }
  }

  const handleUpdateStatus = async (newStatus: RequirementStatus, _comment?: string) => {
    if (!reqId || !requirement) return
    setIsUpdatingStatus(true)
    try {
      const updated = await requirementService.updateStatus(reqId, newStatus)
      setRequirement(updated)
      await loadSolutions(reqId)
      setHistory((prev) => [
        ...prev,
        {
          status: updated.status,
          changed_at: updated.updated_at || new Date().toISOString(),
          changed_by: updated.created_by || '',
        },
      ])
    } catch (error) {
      console.error(error)
    } finally {
      setIsUpdatingStatus(false)
      setShowStatusModal(false)
    }
  }

  const handleAssign = async (assignee: string) => {
    if (!reqId || !requirement) return
    try {
      const updated = await requirementService.assignRequirement(reqId, assignee)
      setRequirement(updated)
    } catch (error) {
      console.error(error)
    } finally {
      setShowAssignModal(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
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

  if (!requirement) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">需求不存在</h3>
          <p className="text-gray-500 mb-6">找不到该需求，请检查链接是否正确</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors"
          >
            返回上一页
          </button>
        </div>
      </div>
    )
  }

  const allStatuses: RequirementStatus[] = [
    'pending', 'analyzing', 'designing', 'reviewing', 'coding', 'testing', 'completed', 'closed'
  ]

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-5xl mx-auto">
        <button
          onClick={() => navigate(`/projects/${requirement.project_id}/requirements`)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回需求列表
        </button>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <TypeIcon type={requirement.type} showLabel size="lg" />
              <PriorityBadge priority={requirement.priority} size="lg" />
              <StatusBadge status={requirement.status} size="lg" />
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowAssignModal(true)}
                className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                👤 分配
              </button>
              <button
                onClick={() => setShowStatusModal(true)}
                className="px-3 py-1.5 text-sm font-medium text-primary bg-primary-light hover:bg-primary/20 rounded-lg transition-colors"
              >
                📝 更新状态
              </button>
            </div>
          </div>

          <h1 className="text-2xl font-semibold text-gray-800 mb-2">
            {requirement.title}
          </h1>

          <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
            {requirement.source && (
              <span className="flex items-center gap-1.5">
                <span>📎</span>
                {requirement.source}
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <span>👤</span>
              创建者: {requirement.created_by}
            </span>
            <span className="flex items-center gap-1.5">
              <span>📅</span>
              {formatDate(requirement.created_at)}
            </span>
          </div>

          {requirement.assignee && (
            <div className="flex items-center gap-2 mb-6 p-3 bg-gray-50 rounded-lg">
              <div className="w-8 h-8 bg-primary-light rounded-full flex items-center justify-center text-sm font-medium text-primary">
                {requirement.assignee.charAt(0).toUpperCase()}
              </div>
              <div>
                <div className="text-xs text-gray-500">负责人</div>
                <div className="text-sm font-medium text-gray-800">{requirement.assignee}</div>
              </div>
            </div>
          )}

          <div className="prose prose-sm max-w-none">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">需求描述</h3>
            <div className="p-4 bg-gray-50 rounded-lg text-gray-700 whitespace-pre-wrap">
              {requirement.description}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <section className="bg-white rounded-xl border border-gray-200 p-4">
            <h2 className="text-sm font-semibold text-gray-800 mb-2">基本信息</h2>
            <p className="text-sm text-gray-600 whitespace-pre-wrap">{requirement.description}</p>
          </section>
          <section className="bg-white rounded-xl border border-gray-200 p-4">
            <h2 className="text-sm font-semibold text-gray-800 mb-2">分析结果</h2>
            {requirement.analysis_result ? (
              <AnalysisCard analysis={requirement.analysis_result} />
            ) : (
              <p className="text-sm text-gray-400">还没有分析结果</p>
            )}
          </section>
          <section className="bg-white rounded-xl border border-gray-200 p-4">
            <h2 className="text-sm font-semibold text-gray-800 mb-2">下一步</h2>
            <p className="text-sm text-gray-600">
              {requirement.type === 'question' && '咨询只回答，不生成方案或代码。'}
              {requirement.type !== 'question' && requirement.status === 'reviewing' && '方案或代码正在等待人工审批。'}
              {requirement.type !== 'question' && (requirement.status === 'pending' || requirement.status === 'analyzing' || requirement.status === 'designing') && solutions.some((item) => item.status === 'draft') && '方案已回到草稿，不再待审核。再次把需求改为审核中后，会重新提交这份方案。'}
              {requirement.type !== 'question' && (requirement.status === 'pending' || requirement.status === 'analyzing' || requirement.status === 'designing') && !solutions.some((item) => item.status === 'draft') && '生成方案后进入审批。'}
              {requirement.type !== 'question' && requirement.status === 'coding' && '代码生成和语法检查进行中，随后进入代码审批。'}
              {requirement.type !== 'question' && requirement.status === 'testing' && '测试作为质量门禁自动执行。'}
              {requirement.status === 'completed' && '流程已完成。'}
              {requirement.status === 'closed' && '需求已关闭。'}
            </p>
            {solutions[0] && (
              <button type="button" onClick={() => navigate(`/solutions/${solutions[0].id}`)} className="mt-3 text-sm text-primary">查看方案</button>
            )}
          </section>
        </div>

        <div className="mb-6">
          <StatusTimeline history={history} currentStatus={requirement.status} />
        </div>

        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-gray-800">解决方案</h2>
              {solutions.length > 0 && (
                <span className="px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600">
                  {solutions.length} 个方案
                </span>
              )}
            </div>
            <GenerateButton
              onClick={handleGenerateSolution}
              isLoading={isGeneratingSolution}
              disabled={solutions.some((item) => item.status === 'pending_review')}
              label="生成方案"
            />
          </div>
          {solutionActors && (
            <p className="mb-4 text-sm text-gray-500">
              生成方案使用 {solutionActors.agent}，技能「{solutionActors.skill}」
            </p>
          )}
          {solutions.some((item) => item.status === 'pending_review') && (
            <p className="mb-4 text-sm text-amber-700">
              已有待审核方案。若要重新生成，请打开该方案；重新生成后，之前的方案会作废。
            </p>
          )}

          {isGeneratingSolution && solutionActors && (
            <FlowStateBanner
              mode="running"
              title="正在生成方案"
              detail={`正在使用 ${solutionActors.agent}，技能「${solutionActors.skill}」。完成后会出现在下方，并进入审批。`}
            />
          )}
          {(generateError || requirement.failure_reason) && (
            <FlowStateBanner
              mode="failed"
              title="方案生成失败"
              detail={generateError || requirement.failure_reason}
              onRetry={handleGenerateSolution}
            />
          )}
          {solutionError ? (
            <div className="bg-white rounded-xl border border-red-200 p-8 text-center">
              <div className="text-4xl mb-3">⚠️</div>
              <h3 className="text-gray-800 font-medium mb-2">加载失败</h3>
              <p className="text-sm text-red-600 mb-4">{solutionError}</p>
              <button
                onClick={() => reqId && loadSolutions(reqId)}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors"
              >
                重试
              </button>
            </div>
          ) : isLoadingSolutions ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : solutions.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
              <div className="text-4xl mb-3">💡</div>
              <h3 className="text-gray-800 font-medium mb-2">暂无解决方案</h3>
              <p className="text-sm text-gray-500 mb-4">
                点击「生成方案」按钮，让 AI 分析需求并生成解决方案
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {solutions.map((solution) => (
                <SolutionCard key={solution.id} solution={solution} />
              ))}
            </div>
          )}
        </div>
      </div>

      {showAssignModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">分配负责人</h3>
            <div className="space-y-2">
              {teamMembers.map((member) => (
                <button
                  key={member}
                  onClick={() => handleAssign(member)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    requirement.assignee === member
                      ? 'bg-primary-light border-2 border-primary'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="w-8 h-8 bg-primary-light rounded-full flex items-center justify-center text-sm font-medium text-primary">
                    {member.charAt(0)}
                  </div>
                  <span className="text-sm font-medium text-gray-800">{member}</span>
                  {requirement.assignee === member && (
                    <span className="ml-auto text-primary">✓</span>
                  )}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowAssignModal(false)}
              className="w-full mt-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {showStatusModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">更新状态</h3>
            <div className="space-y-2">
              {allStatuses.map((status) => {
                const config = statusConfig[status]
                return (
                  <button
                    key={status}
                    disabled={isUpdatingStatus}
                    onClick={() => handleUpdateStatus(status)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                      requirement.status === status
                        ? 'bg-primary-light border-2 border-primary'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <span className={`w-2.5 h-2.5 rounded-full ${config.dotColor}`}></span>
                    <span className="text-sm font-medium text-gray-800">{config.label}</span>
                    {requirement.status === status && (
                      <span className="ml-auto text-primary">✓</span>
                    )}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setShowStatusModal(false)}
              className="w-full mt-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
