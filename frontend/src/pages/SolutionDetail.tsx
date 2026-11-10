import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { BugFixSolution, FeatureDesignSolution, SolutionStatus, CodeGenTaskSummary } from '../types'
import { solutionService, codegenService } from '../services'
import {
  SolutionStatusBadge,
  BugFixView,
  FeatureDesignView,
  ImpactAnalysis,
  AffectedFiles,
  statusConfig,
} from '../components/Solutions'
import { CodeGenStatusBadge } from '../components/CodeGen'
import FlowStateBanner from '../components/FlowStateBanner'

type SolutionData = BugFixSolution | FeatureDesignSolution

export default function SolutionDetail() {
  const { solutionId } = useParams<{ solutionId: string }>()
  const navigate = useNavigate()
  const [solution, setSolution] = useState<SolutionData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUpdating, setIsUpdating] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [codeGenTasks, setCodeGenTasks] = useState<CodeGenTaskSummary[]>([])
  const [isGeneratingCode, setIsGeneratingCode] = useState(false)
  const [isLoadingTasks, setIsLoadingTasks] = useState(false)
  const [actionError, setActionError] = useState('')

  useEffect(() => {
    if (solutionId) {
      loadSolution(solutionId)
      loadCodeGenTasks(solutionId)
    }
  }, [solutionId])

  const loadSolution = async (id: string) => {
    setIsLoading(true)
    try {
      const data = await solutionService.getSolution(id)
      setSolution(data)
    } catch (error) {
      console.error(error)
      setSolution(null)
    } finally {
      setIsLoading(false)
    }
  }

  const loadCodeGenTasks = async (id: string) => {
    setIsLoadingTasks(true)
    try {
      const tasks = await codegenService.getTasksBySolution(id)
      setCodeGenTasks(tasks)
    } catch (error) {
      console.error(error)
      setCodeGenTasks([])
    } finally {
      setIsLoadingTasks(false)
    }
  }

  const handleGenerateCode = async () => {
    if (!solutionId) return
    setIsGeneratingCode(true)
    setActionError('')
    try {
      const task = await codegenService.createCodeGenTask(solutionId)
      navigate(`/codegen/${task.id}`)
    } catch (error) {
      console.error(error)
      setActionError('代码生成没有启动，请确认方案已通过审批')
    } finally {
      setIsGeneratingCode(false)
    }
  }

  const handleUpdateStatus = async (newStatus: SolutionStatus) => {
    if (!solutionId || !solution) return
    setIsUpdating(true)
    try {
      const updated = await solutionService.updateSolutionStatus(solutionId, newStatus)
      setSolution(updated as SolutionData)
    } catch (error) {
      console.error(error)
    } finally {
      setIsUpdating(false)
      setShowStatusModal(false)
    }
  }

  const handleRegenerate = async () => {
    if (!solutionId) return
    setIsRegenerating(true)
    setActionError('')
    try {
      const newSolution = await solutionService.regenerateSolution(solutionId)
      setSolution(newSolution as SolutionData)
    } catch {
      setActionError('方案重新生成失败')
    } finally {
      setIsRegenerating(false)
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

  const typeConfig = {
    bug_fix: { icon: '🐛', label: 'Bug 修复方案' },
    feature_design: { icon: '✨', label: '功能设计方案' },
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

  if (!solution) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">方案不存在</h3>
          <p className="text-gray-500 mb-6">找不到该方案，请检查链接是否正确</p>
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

  const config = typeConfig[solution.type] || { icon: '📄', label: '方案' }
  const allStatuses: SolutionStatus[] = ['draft', 'pending_review']

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-5xl mx-auto">
        <button
          onClick={() => navigate(`/requirements/${solution.requirement_id}`)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回需求详情
        </button>

        {isRegenerating && <FlowStateBanner mode="running" title="正在重新生成方案" />}
        {isGeneratingCode && <FlowStateBanner mode="running" title="正在生成代码" detail="完成后会进入代码页。" />}
        {actionError && <FlowStateBanner mode="failed" title="操作失败" detail={actionError} onRetry={handleRegenerate} />}
        {solution.status === 'rejected' && (
          <FlowStateBanner mode="failed" title="方案未通过" detail="可以按审批意见重新生成。" onRetry={handleRegenerate} retryLabel="重新生成" />
        )}
        {!solution.content && !isRegenerating && (
          <FlowStateBanner mode="failed" title="方案内容为空" detail="重新生成后再进入审批。" onRetry={handleRegenerate} retryLabel="重新生成" />
        )}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{config.icon}</span>
              <span className="text-sm font-medium text-gray-500">{config.label}</span>
              <SolutionStatusBadge status={solution.status} size="lg" />
            </div>
            <div className="flex items-center gap-2">
              {solution.status === 'approved' && (
                <button
                  onClick={handleGenerateCode}
                  disabled={isGeneratingCode}
                  className="px-3 py-1.5 text-sm font-medium text-white bg-green-500 hover:bg-green-600 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  {isGeneratingCode ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      生成中...
                    </>
                  ) : (
                    <>⚙️ 生成代码</>
                  )}
                </button>
              )}
              <button
                onClick={handleRegenerate}
                disabled={isRegenerating}
                className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                {isRegenerating ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                    重新生成中...
                  </>
                ) : (
                  <>
                    🔄 重新生成
                  </>
                )}
              </button>
              <button
                onClick={() => setShowStatusModal(true)}
                className="px-3 py-1.5 text-sm font-medium text-primary bg-primary-light hover:bg-primary/20 rounded-lg transition-colors"
              >
                📝 更新状态
              </button>
            </div>
          </div>

          <h1 className="text-2xl font-semibold text-gray-800 mb-2">{solution.title}</h1>

          <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
            <span className="flex items-center gap-1.5">
              <span>🤖</span>
              {solution.created_by_agent}
            </span>
            <span className="flex items-center gap-1.5">
              <span>📅</span>
              {formatDate(solution.created_at)}
            </span>
            {solution.reviewed_by && (
              <span className="flex items-center gap-1.5">
                <span>👤</span>
                审核人: {solution.reviewed_by}
              </span>
            )}
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-gray-700 whitespace-pre-wrap">{solution.content}</p>
          </div>
        </div>

        <div className="space-y-6">
          {solution.type === 'bug_fix' && (
            <BugFixView solution={solution as BugFixSolution} />
          )}

          {solution.type === 'feature_design' && (
            <FeatureDesignView solution={solution as FeatureDesignSolution} />
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ImpactAnalysis analysis={solution.impact_analysis} />
            <AffectedFiles files={solution.affected_files} />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-center">
          {solution.status === 'pending_review' && (
            <button
              onClick={() => navigate('/reviews')}
              className="px-6 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors"
            >
              到 Review 工作台审批
            </button>
          )}
          {solution.status === 'approved' && (
            <p className="text-sm text-gray-500">方案已通过，代码生成和测试会按审批结果自动继续。</p>
          )}
        </div>

        {(codeGenTasks.length > 0 || isLoadingTasks) && (
          <div className="mt-6 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <span>⚙️</span>
                代码生成任务
              </h3>
              {solution.status === 'approved' && (
                <button
                  onClick={handleGenerateCode}
                  disabled={isGeneratingCode}
                  className="px-3 py-1.5 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  {isGeneratingCode ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      创建中...
                    </>
                  ) : (
                    <>+ 新建任务</>
                  )}
                </button>
              )}
            </div>
            <div className="divide-y divide-gray-100">
              {isLoadingTasks ? (
                <div className="p-6 text-center text-gray-400">
                  <div className="w-6 h-6 border-2 border-gray-300 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  加载中...
                </div>
              ) : codeGenTasks.length === 0 ? (
                <div className="p-6 text-center text-gray-400">
                  暂无代码生成任务
                </div>
              ) : (
                codeGenTasks.map((task) => (
                  <button
                    key={task.id}
                    onClick={() => navigate(`/codegen/${task.id}`)}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
                  >
                    <div className="flex items-center gap-4">
                      <CodeGenStatusBadge status={task.status} />
                      <span className="text-sm font-mono text-gray-500">{task.id}</span>
                      <span className="text-sm text-gray-500">
                        {task.steps && task.steps.length > 0
                          ? `${task.steps.filter((step) => step.status === 'completed').length}/${task.steps.length} 步`
                          : `${task.files_count ?? task.files?.length ?? 0} 个文件`}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-400">
                        {new Date(task.created_at).toLocaleString('zh-CN', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      <span className="text-gray-300">→</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}
      </div>

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
                    onClick={() => handleUpdateStatus(status)}
                    disabled={isUpdating}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                      solution.status === status
                        ? 'bg-primary-light border-2 border-primary'
                        : 'bg-gray-50 hover:bg-gray-100'
                    } disabled:opacity-50`}
                  >
                    <span className={`w-2 h-2 rounded-full ${config.dotColor}`} />
                    <span className="text-sm font-medium text-gray-800">{config.label}</span>
                    {solution.status === status && (
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
