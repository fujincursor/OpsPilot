import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { CIPipeline, TestTask, TestReport, TestStatus } from '../types'
import { testService } from '../services'
import {
  TestStatusBadge,
  TestProgress,
  TestReportCard,
  TestCaseList,
} from '../components/Tests'
import FlowStateBanner from '../components/FlowStateBanner'

export default function TestDetail() {
  const { testTaskId } = useParams<{ testTaskId: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<TestTask | null>(null)
  const [report, setReport] = useState<TestReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRerunning, setIsRerunning] = useState(false)
  const [isTriggeringCI, setIsTriggeringCI] = useState(false)
  const [pipeline, setPipeline] = useState<CIPipeline | null>(null)
  const [ciError, setCiError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadTask = useCallback(async (id: string, silent = false) => {
    if (!silent) setIsLoading(true)
    try {
      const taskData = await testService.getTestTask(id)
      setTask(taskData)
      if (taskData.status === 'completed') {
        try {
          setReport(await testService.getTestReport(id))
        } catch {
          setReport(null)
        }
        setPipeline(await testService.getCI(id))
      }
    } catch (error) {
      console.error(error)
      if (!silent) {
        setTask(null)
        setReport(null)
      }
    } finally {
      if (!silent) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (testTaskId) {
      loadTask(testTaskId)
    }
  }, [testTaskId, loadTask])

  useEffect(() => {
    if (!task || task.status === 'completed' || task.status === 'failed') return

    const pollInterval = setInterval(() => {
      if (testTaskId) loadTask(testTaskId, true)
    }, 3000)

    return () => clearInterval(pollInterval)
  }, [task, testTaskId, loadTask])

  const handleRerun = async () => {
    if (!testTaskId) return
    setIsRerunning(true)
    try {
      const newTask = await testService.rerunTests(testTaskId)
      setTask(newTask)
    } catch {
      setTask((current) => current ? { ...current, status: 'failed' } : current)
    } finally {
      setIsRerunning(false)
    }
  }

  const handleTriggerCI = async () => {
    if (!testTaskId) return
    setIsTriggeringCI(true)
    setCiError('')
    try {
      const nextPipeline = await testService.triggerCI(testTaskId)
      setPipeline(nextPipeline)
      await loadTask(testTaskId, true)
      setPipeline(nextPipeline)
    } catch {
      setCiError('流水线没有跑起来，请再试一次')
    } finally {
      setIsTriggeringCI(false)
    }
  }

  const handleSubmitForReview = async () => {
    if (!testTaskId) return
    setIsSubmitting(true)
    try {
      await testService.submitForReview(testTaskId)
      navigate('/reviews')
    } catch {
      console.log('Submit failed')
    } finally {
      setIsSubmitting(false)
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

  const isInProgress = (status: TestStatus) => {
    return status === 'pending' || status === 'generating' || status === 'running'
  }

  const canSubmitForReview = () => {
    if (!task || !report) return false
    return task.status === 'completed' && report.failed === 0 && report.coverage_percent >= 60
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
          <h3 className="text-lg font-medium text-gray-800 mb-2">测试任务不存在</h3>
          <p className="text-gray-500 mb-6">找不到该测试任务</p>
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

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate(`/codegen/${task.codegen_task_id}`)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回代码生成
        </button>

        {(task.status === 'pending' || task.status === 'generating' || task.status === 'running' || isRerunning) && (
          <FlowStateBanner mode="running" title={task.status === 'running' ? '正在执行测试' : '正在生成测试'} detail="失败用例会留在这一页，通过质量门禁后流程继续。" />
        )}
        {task.status === 'failed' && (
          <FlowStateBanner
            mode="failed"
            title="测试未通过"
            detail={task.results.filter((item) => item.status === 'failed').map((item) => `${item.test_case_id} ${item.error_message || item.actual_result || '失败'}`).join('\n') || '没有记录失败用例'}
            onRetry={handleRerun}
            retryLabel="重新运行"
          />
        )}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🧪</span>
              <span className="text-sm font-medium text-gray-500">测试任务</span>
              <TestStatusBadge status={task.status} size="lg" />
            </div>
            <div className="flex items-center gap-2">
              {(task.status === 'failed' || task.status === 'completed') && (
                <>
                  <button
                    onClick={handleRerun}
                    disabled={isRerunning}
                    className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {isRerunning ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                        重新运行中...
                      </>
                    ) : (
                      <>🔄 重新运行</>
                    )}
                  </button>
                  <button
                    onClick={handleTriggerCI}
                    disabled={isTriggeringCI}
                    className="px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {isTriggeringCI ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                        触发中...
                      </>
                    ) : (
                      <>🚀 触发 CI</>
                    )}
                  </button>
                  {canSubmitForReview() && (
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
                  )}
                </>
              )}
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
              <span>🧪</span>
              {task.test_cases.length} 个用例
            </span>
            {task.sandbox_profile && (
              <span className="flex items-center gap-1.5">
                <span>📦</span>
                {task.sandbox_profile}
              </span>
            )}
          </div>
        </div>

        {(pipeline || ciError || isTriggeringCI) && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">CI 流水线</h3>
              {pipeline && (
                <span className="text-sm text-gray-500">{pipeline.pipeline_id}</span>
              )}
            </div>
            {ciError && <p className="text-sm text-red-600">{ciError}</p>}
            {isTriggeringCI && !pipeline && (
              <p className="text-sm text-gray-500">正在沙箱里重新运行检查...</p>
            )}
            {pipeline && (
              <div className="space-y-3">
                {pipeline.stages.map((stage) => (
                  <div key={stage.name} className="flex items-start justify-between gap-4 rounded-lg border border-gray-100 px-4 py-3">
                    <div>
                      <div className="font-medium text-gray-800">{stage.name}</div>
                      {stage.detail && <p className="mt-1 text-sm text-gray-500">{stage.detail}</p>}
                    </div>
                    <span className={`text-sm font-medium ${stage.status === 'passed' ? 'text-green-600' : stage.status === 'failed' ? 'text-red-600' : 'text-gray-500'}`}>
                      {stage.status === 'passed' && '通过'}
                      {stage.status === 'failed' && '失败'}
                      {stage.status === 'running' && '运行中'}
                      {stage.status === 'pending' && '等待'}
                      {stage.status === 'skipped' && '跳过'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <TestProgress status={task.status} className="mb-6" />

        {isInProgress(task.status) ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-800 mb-2">
              {task.status === 'pending' && '准备测试...'}
              {task.status === 'generating' && '正在生成测试用例...'}
              {task.status === 'running' && '正在运行测试...'}
            </h3>
            <p className="text-gray-500">请稍候，这可能需要几分钟时间</p>
          </div>
        ) : (
          <div className="space-y-6">
            {report && <TestReportCard report={report} />}

            <TestCaseList testCases={task.test_cases} results={task.results} />
          </div>
        )}
      </div>
    </div>
  )
}
