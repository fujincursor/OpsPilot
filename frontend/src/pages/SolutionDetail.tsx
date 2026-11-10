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

const mockBugFixSolution: BugFixSolution = {
  id: 'sol-1',
  requirement_id: 'req-1',
  type: 'bug_fix',
  title: '修复用户登录超时问题',
  content: '通过优化 Token 刷新机制和会话管理来解决用户登录后过早被登出的问题。',
  impact_analysis: '本次修复主要影响认证模块和会话管理模块。\n\n修改后，Token 刷新逻辑将更加可靠，减少因竞态条件导致的会话失效问题。\n\n预计可以将用户被意外登出的情况减少 95% 以上。',
  affected_files: [
    'src/services/authService.ts',
    'src/utils/tokenManager.ts',
    'src/middleware/authMiddleware.ts',
    'src/hooks/useAuth.ts',
  ],
  status: 'pending_review',
  created_by_agent: 'BugFix Agent',
  created_at: '2024-03-16T15:30:00Z',
  root_cause: '问题根因分析：\n\n1. Token 刷新逻辑存在竞态条件，当多个请求同时检测到 Token 即将过期时，会同时发起刷新请求\n\n2. 刷新请求失败时没有正确处理重试逻辑，直接将用户登出\n\n3. 高并发场景下，后端的 Token 验证和刷新接口存在性能瓶颈，导致响应超时',
  fix_steps: [
    {
      order: 1,
      description: '在 tokenManager.ts 中添加请求锁机制，防止并发刷新请求',
      file_path: 'src/utils/tokenManager.ts',
      code_snippet: `let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

async function refreshToken() {
  if (isRefreshing) {
    return new Promise<string>((resolve) => {
      subscribeTokenRefresh(resolve)
    })
  }
  
  isRefreshing = true
  try {
    const newToken = await authApi.refresh()
    refreshSubscribers.forEach(cb => cb(newToken))
    return newToken
  } finally {
    isRefreshing = false
    refreshSubscribers = []
  }
}`,
    },
    {
      order: 2,
      description: '修改 authMiddleware.ts，添加重试逻辑和更优雅的错误处理',
      file_path: 'src/middleware/authMiddleware.ts',
      code_snippet: `const MAX_RETRY = 3

async function handleAuthError(error: AuthError, retryCount = 0) {
  if (retryCount >= MAX_RETRY) {
    return logout()
  }
  
  if (error.code === 'TOKEN_EXPIRED') {
    const newToken = await refreshToken()
    return retryRequest(error.config, newToken)
  }
  
  throw error
}`,
    },
    {
      order: 3,
      description: '更新 useAuth hook，添加会话状态监控和自动恢复功能',
      file_path: 'src/hooks/useAuth.ts',
    },
  ],
  regression_risk: {
    level: 'medium',
    description: '修改涉及核心认证逻辑，需要进行完整的回归测试，特别是多标签页同时操作、网络不稳定等边缘场景。',
    affected_areas: ['用户登录流程', 'API 请求拦截', 'Token 存储与刷新', '多标签页同步'],
  },
}

const mockFeatureDesignSolution: FeatureDesignSolution = {
  id: 'sol-2',
  requirement_id: 'req-2',
  type: 'feature_design',
  title: '用户权限管理系统设计',
  content: '设计并实现基于 RBAC 的用户权限管理系统，支持角色定义、权限分配和细粒度访问控制。',
  impact_analysis: '本功能涉及用户管理、权限控制、菜单展示等多个模块。\n\n需要新增数据库表结构，并对现有的用户认证流程进行扩展。\n\n上线后需要进行权限数据迁移，将现有用户的权限映射到新的 RBAC 模型中。',
  affected_files: [
    'src/services/permissionService.ts',
    'src/services/roleService.ts',
    'src/components/PermissionGuard.tsx',
    'src/hooks/usePermission.ts',
    'src/pages/admin/RoleManagement.tsx',
  ],
  status: 'draft',
  created_by_agent: 'Feature Agent',
  created_at: '2024-03-16T16:00:00Z',
  architecture: {
    overview: '采用 RBAC（基于角色的访问控制）模型，通过角色作为用户和权限之间的桥梁，实现灵活的权限管理。\n\n系统分为三层：\n1. 权限层：定义原子级别的操作权限\n2. 角色层：将权限组合成角色\n3. 用户层：为用户分配一个或多个角色',
    components: [
      {
        name: 'PermissionService',
        description: '权限核心服务，负责权限的定义、验证和缓存',
        responsibilities: ['权限验证', '权限缓存', '权限树构建'],
      },
      {
        name: 'RoleService',
        description: '角色管理服务，处理角色的 CRUD 和角色-权限关联',
        responsibilities: ['角色管理', '权限分配', '角色继承'],
      },
      {
        name: 'PermissionGuard',
        description: 'React 权限守卫组件，用于前端权限控制',
        responsibilities: ['组件级权限控制', '路由权限控制', '按钮权限控制'],
      },
    ],
  },
  api_design: [
    {
      method: 'GET',
      endpoint: '/api/v1/roles',
      description: '获取角色列表，支持分页和搜索',
      response_body: `{
  "data": [
    {
      "id": "role-1",
      "name": "admin",
      "description": "系统管理员",
      "permissions": ["user:read", "user:write"]
    }
  ],
  "total": 10
}`,
    },
    {
      method: 'POST',
      endpoint: '/api/v1/roles',
      description: '创建新角色',
      request_body: `{
  "name": "editor",
  "description": "内容编辑",
  "permissions": ["content:read", "content:write"]
}`,
      response_body: `{
  "data": {
    "id": "role-2",
    "name": "editor",
    "description": "内容编辑",
    "permissions": ["content:read", "content:write"]
  }
}`,
    },
    {
      method: 'PATCH',
      endpoint: '/api/v1/users/:id/roles',
      description: '为用户分配角色',
      request_body: `{
  "roleIds": ["role-1", "role-2"]
}`,
    },
  ],
  database_changes: [
    {
      type: 'create_table',
      table_name: 'roles',
      description: '角色表，存储角色基本信息',
      sql: `CREATE TABLE roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) NOT NULL UNIQUE,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);`,
    },
    {
      type: 'create_table',
      table_name: 'role_permissions',
      description: '角色-权限关联表',
      sql: `CREATE TABLE role_permissions (
  role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
  permission VARCHAR(100) NOT NULL,
  PRIMARY KEY (role_id, permission)
);`,
    },
    {
      type: 'create_table',
      table_name: 'user_roles',
      description: '用户-角色关联表',
      sql: `CREATE TABLE user_roles (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);`,
    },
  ],
  dependencies: ['@casl/ability', '@casl/react', 'zustand'],
}

type SolutionData = BugFixSolution | FeatureDesignSolution

const mockCodeGenTasks: CodeGenTaskSummary[] = [
  {
    id: 'cg-1',
    status: 'completed',
    files_count: 3,
    created_at: '2024-03-16T15:45:00Z',
  },
  {
    id: 'cg-2',
    status: 'failed',
    files_count: 0,
    created_at: '2024-03-16T14:30:00Z',
  },
]

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
    } catch {
      console.log('Using mock data')
      setSolution(id.includes('2') ? mockFeatureDesignSolution : mockBugFixSolution)
    } finally {
      setIsLoading(false)
    }
  }

  const loadCodeGenTasks = async (id: string) => {
    setIsLoadingTasks(true)
    try {
      const tasks = await codegenService.getTasksBySolution(id)
      setCodeGenTasks(tasks)
    } catch {
      console.log('Using mock codegen tasks')
      setCodeGenTasks(mockCodeGenTasks)
    } finally {
      setIsLoadingTasks(false)
    }
  }

  const handleGenerateCode = async () => {
    if (!solutionId) return
    setIsGeneratingCode(true)
    try {
      const task = await codegenService.createCodeGenTask(solutionId)
      navigate(`/codegen/${task.id}`)
    } catch {
      const newTaskId = `cg-${Date.now()}`
      navigate(`/codegen/${newTaskId}`)
    } finally {
      setIsGeneratingCode(false)
    }
  }

  const handleUpdateStatus = async (newStatus: SolutionStatus) => {
    if (!solutionId || !solution) return
    setIsUpdating(true)
    try {
      await solutionService.updateSolutionStatus(solutionId, newStatus)
      setSolution((prev) => prev ? { ...prev, status: newStatus } : null)
    } catch {
      setSolution((prev) => prev ? { ...prev, status: newStatus } : null)
    } finally {
      setIsUpdating(false)
      setShowStatusModal(false)
    }
  }

  const handleRegenerate = async () => {
    if (!solutionId) return
    setIsRegenerating(true)
    try {
      const newSolution = await solutionService.regenerateSolution(solutionId)
      setSolution(newSolution as SolutionData)
    } catch {
      console.log('Regenerate failed, keeping current solution')
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

  const config = typeConfig[solution.type]
  const allStatuses: SolutionStatus[] = ['draft', 'pending_review', 'approved', 'rejected', 'implemented']

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

        <div className="mt-6 flex items-center justify-center gap-4">
          {solution.status === 'pending_review' && (
            <>
              <button
                onClick={() => handleUpdateStatus('approved')}
                disabled={isUpdating}
                className="px-6 py-2.5 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                ✅ 通过方案
              </button>
              <button
                onClick={() => handleUpdateStatus('rejected')}
                disabled={isUpdating}
                className="px-6 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                ❌ 拒绝方案
              </button>
            </>
          )}
          {solution.status === 'approved' && (
            <button
              onClick={() => handleUpdateStatus('implemented')}
              disabled={isUpdating}
              className="px-6 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              🚀 标记为已实现
            </button>
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
                        {task.files_count} 个文件
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
