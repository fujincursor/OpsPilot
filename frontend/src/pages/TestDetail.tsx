import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { TestTask, TestReport, TestStatus } from '../types'
import { testService } from '../services'
import {
  TestStatusBadge,
  TestProgress,
  TestReportCard,
  TestCaseList,
} from '../components/Tests'

const mockTestTask: TestTask = {
  id: 'test-1',
  codegen_task_id: 'cg-1',
  requirement_id: 'req-1',
  status: 'completed',
  test_cases: [
    {
      id: 'tc-1',
      name: 'refreshToken should return new token',
      description: '测试 refreshToken 函数能正确刷新并返回新的 token',
      type: 'unit',
      code: `describe('refreshToken', () => {
  it('should return new token when refresh succeeds', async () => {
    fetchMock.mockResponseOnce(JSON.stringify({ token: 'new-token' }));
    const result = await refreshToken();
    expect(result).toBe('new-token');
  });
});`,
      expected_result: 'new-token',
    },
    {
      id: 'tc-2',
      name: 'refreshToken should handle concurrent requests',
      description: '测试并发请求时只发送一次刷新请求',
      type: 'unit',
      code: `describe('refreshToken concurrent', () => {
  it('should only make one request for concurrent calls', async () => {
    fetchMock.mockResponseOnce(JSON.stringify({ token: 'token' }));
    const results = await Promise.all([refreshToken(), refreshToken()]);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(results).toEqual(['token', 'token']);
  });
});`,
      expected_result: '只调用一次 fetch',
    },
    {
      id: 'tc-3',
      name: 'isTokenExpiring should detect expiring token',
      description: '测试 isTokenExpiring 能正确检测即将过期的 token',
      type: 'unit',
      code: `describe('isTokenExpiring', () => {
  it('should return true for token expiring in 3 minutes', () => {
    const exp = Math.floor(Date.now() / 1000) + 180;
    const token = btoa(JSON.stringify({ exp }));
    expect(isTokenExpiring(\`header.\${token}.sig\`)).toBe(true);
  });
});`,
      expected_result: 'true',
    },
    {
      id: 'tc-4',
      name: 'handleAuthError should retry on TOKEN_EXPIRED',
      description: '测试 handleAuthError 在 token 过期时能重试请求',
      type: 'integration',
      code: `describe('handleAuthError', () => {
  it('should retry request with new token on TOKEN_EXPIRED', async () => {
    const error = { code: 'TOKEN_EXPIRED', config: { url: '/api/data' } };
    const response = await handleAuthError(error);
    expect(response.ok).toBe(true);
  });
});`,
      expected_result: 'response.ok === true',
    },
    {
      id: 'tc-5',
      name: 'useAuth should initialize auth state',
      description: '测试 useAuth hook 能正确初始化认证状态',
      type: 'integration',
      code: `describe('useAuth', () => {
  it('should initialize with loading state', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.isLoading).toBe(true);
  });
});`,
      expected_result: 'isLoading === true',
    },
  ],
  results: [
    {
      test_case_id: 'tc-1',
      status: 'passed',
      actual_result: 'new-token',
      duration: 45,
    },
    {
      test_case_id: 'tc-2',
      status: 'passed',
      actual_result: '只调用一次 fetch',
      duration: 52,
    },
    {
      test_case_id: 'tc-3',
      status: 'failed',
      actual_result: 'false',
      error_message: 'AssertionError: expected false to be true\n    at Context.<anonymous> (test/tokenManager.test.ts:45:28)',
      duration: 38,
    },
    {
      test_case_id: 'tc-4',
      status: 'passed',
      actual_result: 'response.ok === true',
      duration: 125,
    },
    {
      test_case_id: 'tc-5',
      status: 'skipped',
      actual_result: 'Skipped due to dependency failure',
      duration: 0,
    },
  ],
  coverage: 78.5,
  created_at: '2024-03-16T16:30:00Z',
}

const mockTestReport: TestReport = {
  task_id: 'test-1',
  total: 5,
  passed: 3,
  failed: 1,
  skipped: 1,
  coverage_percent: 78.5,
  duration: 260,
}

export default function TestDetail() {
  const { testTaskId } = useParams<{ testTaskId: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<TestTask | null>(null)
  const [report, setReport] = useState<TestReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRerunning, setIsRerunning] = useState(false)
  const [isTriggeringCI, setIsTriggeringCI] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadTask = useCallback(async (id: string) => {
    setIsLoading(true)
    try {
      const [taskData, reportData] = await Promise.all([
        testService.getTestTask(id),
        testService.getTestReport(id),
      ])
      setTask(taskData)
      setReport(reportData)
    } catch {
      console.log('Using mock data')
      setTask(mockTestTask)
      setReport(mockTestReport)
    } finally {
      setIsLoading(false)
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
      if (testTaskId) loadTask(testTaskId)
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
      console.log('Rerun failed')
    } finally {
      setIsRerunning(false)
    }
  }

  const handleTriggerCI = async () => {
    if (!testTaskId) return
    setIsTriggeringCI(true)
    try {
      const { ci_url } = await testService.triggerCI(testTaskId)
      window.open(ci_url, '_blank')
    } catch {
      console.log('Trigger CI failed')
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
          </div>
        </div>

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
