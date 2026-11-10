import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { CodeGenTask, CodeFile, CodeGenStatus, TestTaskSummary } from '../types'
import { codegenService, testService } from '../services'
import {
  CodeGenStatusBadge,
  CodeGenProgress,
  SolutionSteps,
  FileTree,
  CodeViewer,
  DiffViewer,
  LintResultCard,
} from '../components/CodeGen'
import { TestStatusBadge } from '../components/Tests'
import FlowStateBanner from '../components/FlowStateBanner'

type ViewMode = 'code' | 'diff'

export default function CodeGenDetail() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<CodeGenTask | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('code')
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isApplying, setIsApplying] = useState(false)
  const [applyMessage, setApplyMessage] = useState('')
  const [testTasks, setTestTasks] = useState<TestTaskSummary[]>([])
  const [isCreatingTest, setIsCreatingTest] = useState(false)

  const loadTestTasks = useCallback(async (codegenTaskId: string) => {
    try {
      const tasks = await testService.getTasksByCodegen(codegenTaskId)
      setTestTasks(tasks)
    } catch {
      setTestTasks([])
    }
  }, [])

  const loadTask = useCallback(async (id: string, silent = false) => {
    if (!silent) setIsLoading(true)
    try {
      const data = await codegenService.getTaskStatus(id)
      setTask(data)
      if (data.files && data.files.length > 0) {
        setSelectedFile((current) => current || data.files[0].path)
      }
    } catch (error) {
      console.error(error)
      if (!silent) setTask(null)
    } finally {
      if (!silent) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (taskId) {
      loadTask(taskId)
      loadTestTasks(taskId)
    }
  }, [taskId, loadTask, loadTestTasks])

  useEffect(() => {
    if (!task || task.status === 'completed' || task.status === 'failed') return

    const pollInterval = setInterval(() => {
      if (taskId) loadTask(taskId, true)
    }, 3000)

    return () => clearInterval(pollInterval)
  }, [task, taskId, loadTask])

  const handleRegenerate = async () => {
    if (!taskId) return
    setIsRegenerating(true)
    try {
      const newTask = await codegenService.regenerate(taskId)
      setTask(newTask)
    } catch {
      setTask((current) => current ? { ...current, status: 'failed', error_message: current.error_message || '重新生成失败' } : current)
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleApply = async () => {
    if (!taskId || !task) return
    const paths = task.files
      .filter((file) => file.action === 'create' || file.action === 'modify' || file.action === 'delete')
      .map((file) => file.path)
    if (paths.length === 0) return
    const confirmed = window.confirm(`把以下文件写回项目？\n${paths.join('\n')}`)
    if (!confirmed) return
    setIsApplying(true)
    setApplyMessage('')
    try {
      const updated = await codegenService.applyToProject(taskId)
      setTask(updated)
      setApplyMessage(`已写回 ${updated.applied_paths?.length || paths.length} 个文件`)
    } catch {
      setApplyMessage('写回失败，请再试一次')
    } finally {
      setIsApplying(false)
    }
  }

  const handleSubmitForReview = async () => {
    if (!taskId) return
    setIsSubmitting(true)
    try {
      await codegenService.submitForReview(taskId)
      navigate(`/reviews`)
    } catch {
      console.log('Submit failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCreateTest = async () => {
    if (!taskId) return
    setIsCreatingTest(true)
    try {
      const newTestTask = await testService.createTestTask(taskId)
      navigate(`/tests/${newTestTask.id}`)
    } catch {
      console.log('Create test failed')
    } finally {
      setIsCreatingTest(false)
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

  const getSelectedFileData = (): CodeFile | null => {
    if (!task || !selectedFile) return null
    return task.files.find((f) => f.path === selectedFile) || null
  }

  const isInProgress = (status: CodeGenStatus) => {
    return status === 'pending' || status === 'generating' || status === 'linting'
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

  if (!task) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">任务不存在</h3>
          <p className="text-gray-500 mb-6">找不到该代码生成任务</p>
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

  const selectedFileData = getSelectedFileData()

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate(`/solutions/${task.solution_id}`)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回方案详情
        </button>

        {(task.status === 'pending' || task.status === 'generating' || task.status === 'linting' || isRegenerating) && (
          <FlowStateBanner mode="running" title={task.status === 'linting' ? '正在做语法检查' : '正在生成代码'} detail="这一页会保持当前任务，状态变化后自动刷新。" />
        )}
        {task.status === 'failed' && (
          <FlowStateBanner
            mode="failed"
            title="代码生成失败"
            detail={task.error_message || (task.lint_result?.errors || []).map((error) => `${error.file}:${error.line} ${error.message}`).join('\n') || '没有记录失败原因'}
            onRetry={handleRegenerate}
            retryLabel="重新生成"
          />
        )}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚙️</span>
              <span className="text-sm font-medium text-gray-500">代码生成任务</span>
              <CodeGenStatusBadge status={task.status} size="lg" />
            </div>
            <div className="flex items-center gap-2">
              {task.status === 'failed' || task.status === 'completed' ? (
                <>
                  {task.status === 'completed' && task.files.some((file) => file.action !== 'view') && (
                    <button
                      onClick={handleApply}
                      disabled={isApplying}
                      className="px-3 py-1.5 text-sm font-medium text-indigo-600 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
                    >
                      {isApplying ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                          写回中...
                        </>
                      ) : (
                        <>📥 应用代码</>
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
                      <>🔄 重新生成</>
                    )}
                  </button>
                  {task.status === 'completed' && task.lint_result?.passed && (
                    <>
                      <button
                        onClick={handleCreateTest}
                        disabled={isCreatingTest}
                        className="px-3 py-1.5 text-sm font-medium text-green-600 bg-green-100 hover:bg-green-200 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {isCreatingTest ? (
                          <>
                            <div className="w-3.5 h-3.5 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
                            创建中...
                          </>
                        ) : (
                          <>🧪 运行测试</>
                        )}
                      </button>
                      <button
                        onClick={handleSubmitForReview}
                        disabled={isSubmitting}
                        className="px-3 py-1.5 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {isSubmitting ? (
                          <>
                            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            提交中...
                          </>
                        ) : (
                          <>📤 提交审核</>
                        )}
                      </button>
                    </>
                  )}
                </>
              ) : null}
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1.5">
              <span>📋</span>
              任务 ID: {task.id}
            </span>
            <span className="flex items-center gap-1.5">
              <span>📅</span>
              {formatDate(task.created_at)}
            </span>
            <span className="flex items-center gap-1.5">
              <span>🗃️</span>
              {task.files.length} 个文件
            </span>
            <span className="flex items-center gap-1.5">
              <span>💻</span>
              {task.language}
            </span>
            {task.sandbox_profile && (
              <span className="flex items-center gap-1.5">
                <span>📦</span>
                {task.sandbox_profile}
              </span>
            )}
          </div>

          {(applyMessage || (task.applied_paths && task.applied_paths.length > 0)) && (
            <p className={`mt-4 text-sm ${applyMessage.includes('失败') ? 'text-red-600' : 'text-green-700'}`}>
              {applyMessage || `已写回 ${task.applied_paths?.join('、')}`}
            </p>
          )}

          {task.error_message && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <span className="text-red-500">❌</span>
                <div>
                  <p className="font-medium text-red-800">生成失败</p>
                  <p className="text-sm text-red-600 mt-1">{task.error_message}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {testTasks.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <span>🧪</span>
                测试任务
              </h3>
              <span className="text-sm text-gray-500">{testTasks.length} 个任务</span>
            </div>
            <div className="space-y-2">
              {testTasks.map((testTask) => (
                <div
                  key={testTask.id}
                  onClick={() => navigate(`/tests/${testTask.id}`)}
                  className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <TestStatusBadge status={testTask.status} size="sm" />
                    <span className="text-sm text-gray-600">
                      {testTask.total_cases} 个用例
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    {testTask.status === 'completed' && (
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-green-600">✓ {testTask.passed}</span>
                        <span className="text-red-600">✗ {testTask.failed}</span>
                      </div>
                    )}
                    <span className="text-xs text-gray-400">
                      {new Date(testTask.created_at).toLocaleString('zh-CN', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="text-gray-400">→</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <CodeGenProgress status={task.status} className="mb-6" />
        <SolutionSteps steps={task.steps || []} className="mb-6" />

        {isInProgress(task.status) && task.files.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-800 mb-2">
              {task.status === 'pending' && '准备读取方案步骤...'}
              {task.status === 'generating' && '正在按方案步骤执行...'}
              {task.status === 'linting' && '正在进行代码检查...'}
            </h3>
            <p className="text-gray-500">每一步都会单独执行，完成后结果会出现在上面</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-1">
              <FileTree
                files={task.files}
                selectedFile={selectedFile || undefined}
                onSelectFile={setSelectedFile}
              />
            </div>

            <div className="lg:col-span-3 space-y-6">
              <div className="flex items-center gap-2 bg-white rounded-lg border border-gray-200 p-1 w-fit">
                <button
                  onClick={() => setViewMode('code')}
                  className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    viewMode === 'code'
                      ? 'bg-primary text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  📄 代码
                </button>
                <button
                  onClick={() => setViewMode('diff')}
                  className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    viewMode === 'diff'
                      ? 'bg-primary text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  📊 差异
                </button>
              </div>

              {viewMode === 'code' ? (
                <CodeViewer file={selectedFileData} />
              ) : (
                <DiffViewer
                  diff={selectedFileData?.diff || []}
                  fileName={selectedFileData?.path}
                />
              )}

              <LintResultCard
                result={task.lint_result || null}
                isLoading={false}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
