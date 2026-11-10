import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { CodeGenTask, CodeFile, CodeGenStatus } from '../types'
import { codegenService } from '../services'
import {
  CodeGenStatusBadge,
  CodeGenProgress,
  FileTree,
  CodeViewer,
  DiffViewer,
  LintResultCard,
} from '../components/CodeGen'

const mockCodeGenTask: CodeGenTask = {
  id: 'cg-1',
  solution_id: 'sol-1',
  requirement_id: 'req-1',
  status: 'completed',
  language: 'typescript',
  files: [
    {
      path: 'src/utils/tokenManager.ts',
      content: `let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

export async function refreshToken(): Promise<string> {
  if (isRefreshing) {
    return new Promise<string>((resolve) => {
      subscribeTokenRefresh(resolve)
    })
  }
  
  isRefreshing = true
  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    })
    
    if (!response.ok) {
      throw new Error('Token refresh failed')
    }
    
    const { token } = await response.json()
    refreshSubscribers.forEach(cb => cb(token))
    return token
  } finally {
    isRefreshing = false
    refreshSubscribers = []
  }
}

export function isTokenExpiring(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const expiresAt = payload.exp * 1000
    const now = Date.now()
    const threshold = 5 * 60 * 1000 // 5 minutes
    return expiresAt - now < threshold
  } catch {
    return true
  }
}`,
      language: 'typescript',
      action: 'modify',
      diff: [
        { type: 'context', content: 'let isRefreshing = false', line_number: 1 },
        { type: 'context', content: 'let refreshSubscribers: ((token: string) => void)[] = []', line_number: 2 },
        { type: 'context', content: '', line_number: 3 },
        { type: 'add', content: 'function subscribeTokenRefresh(callback: (token: string) => void) {', line_number: 4 },
        { type: 'add', content: '  refreshSubscribers.push(callback)', line_number: 5 },
        { type: 'add', content: '}', line_number: 6 },
        { type: 'add', content: '', line_number: 7 },
        { type: 'context', content: 'export async function refreshToken(): Promise<string> {', line_number: 8 },
        { type: 'remove', content: '  const response = await fetch(\'/api/auth/refresh\')', line_number: 0 },
        { type: 'add', content: '  if (isRefreshing) {', line_number: 9 },
        { type: 'add', content: '    return new Promise<string>((resolve) => {', line_number: 10 },
        { type: 'add', content: '      subscribeTokenRefresh(resolve)', line_number: 11 },
        { type: 'add', content: '    })', line_number: 12 },
        { type: 'add', content: '  }', line_number: 13 },
        { type: 'add', content: '', line_number: 14 },
        { type: 'add', content: '  isRefreshing = true', line_number: 15 },
        { type: 'context', content: '  try {', line_number: 16 },
      ],
    },
    {
      path: 'src/middleware/authMiddleware.ts',
      content: `import { refreshToken } from '../utils/tokenManager'

const MAX_RETRY = 3

interface AuthError extends Error {
  code: string
  config: RequestConfig
}

interface RequestConfig {
  url: string
  method: string
  headers: Record<string, string>
  body?: string
}

export async function handleAuthError(
  error: AuthError,
  retryCount = 0
): Promise<Response> {
  if (retryCount >= MAX_RETRY) {
    await logout()
    throw new Error('Max retry attempts reached')
  }
  
  if (error.code === 'TOKEN_EXPIRED') {
    const newToken = await refreshToken()
    return retryRequest(error.config, newToken)
  }
  
  throw error
}

async function retryRequest(
  config: RequestConfig,
  token: string
): Promise<Response> {
  return fetch(config.url, {
    method: config.method,
    headers: {
      ...config.headers,
      Authorization: \`Bearer \${token}\`,
    },
    body: config.body,
  })
}

async function logout(): Promise<void> {
  localStorage.removeItem('auth_token')
  window.location.href = '/login'
}`,
      language: 'typescript',
      action: 'modify',
    },
    {
      path: 'src/hooks/useAuth.ts',
      content: `import { useState, useEffect, useCallback } from 'react'
import { refreshToken, isTokenExpiring } from '../utils/tokenManager'

interface User {
  id: string
  email: string
  name: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('auth_token')
    
    if (!token) {
      setState({ user: null, isAuthenticated: false, isLoading: false })
      return
    }

    if (isTokenExpiring(token)) {
      try {
        await refreshToken()
      } catch {
        setState({ user: null, isAuthenticated: false, isLoading: false })
        return
      }
    }

    // Decode user from token
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      setState({
        user: { id: payload.sub, email: payload.email, name: payload.name },
        isAuthenticated: true,
        isLoading: false,
      })
    } catch {
      setState({ user: null, isAuthenticated: false, isLoading: false })
    }
  }, [])

  useEffect(() => {
    checkAuth()
    
    // Check auth status periodically
    const interval = setInterval(checkAuth, 60000)
    return () => clearInterval(interval)
  }, [checkAuth])

  return state
}`,
      language: 'typescript',
      action: 'create',
    },
  ],
  lint_result: {
    passed: true,
    errors: [],
    warnings: [
      {
        file: 'src/middleware/authMiddleware.ts',
        line: 45,
        column: 3,
        message: '\'logout\' function should be exported or moved to a separate module',
        rule: 'import/no-internal-modules',
      },
    ],
  },
  created_at: '2024-03-16T15:45:00Z',
}

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

  const loadTask = useCallback(async (id: string) => {
    setIsLoading(true)
    try {
      const data = await codegenService.getTaskStatus(id)
      setTask(data)
      if (data.files.length > 0 && !selectedFile) {
        setSelectedFile(data.files[0].path)
      }
    } catch {
      console.log('Using mock data')
      setTask(mockCodeGenTask)
      if (mockCodeGenTask.files.length > 0 && !selectedFile) {
        setSelectedFile(mockCodeGenTask.files[0].path)
      }
    } finally {
      setIsLoading(false)
    }
  }, [selectedFile])

  useEffect(() => {
    if (taskId) {
      loadTask(taskId)
    }
  }, [taskId, loadTask])

  useEffect(() => {
    if (!task || task.status === 'completed' || task.status === 'failed') return

    const pollInterval = setInterval(() => {
      if (taskId) loadTask(taskId)
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
      console.log('Regenerate failed')
    } finally {
      setIsRegenerating(false)
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
          </div>

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

        <CodeGenProgress status={task.status} className="mb-6" />

        {isInProgress(task.status) ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-800 mb-2">
              {task.status === 'pending' && '准备生成...'}
              {task.status === 'generating' && '正在生成代码...'}
              {task.status === 'linting' && '正在进行代码检查...'}
            </h3>
            <p className="text-gray-500">请稍候，这可能需要几分钟时间</p>
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
