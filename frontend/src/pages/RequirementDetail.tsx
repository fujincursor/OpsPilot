import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { Requirement, RequirementStatus, StatusHistoryItem } from '../types'
import { requirementService } from '../services'
import {
  TypeIcon,
  PriorityBadge,
  StatusBadge,
  AnalysisCard,
  StatusTimeline,
  statusConfig,
} from '../components/Requirements'

const mockRequirement: Requirement = {
  id: '1',
  project_id: '1',
  title: '用户登录超时问题',
  description: '用户反馈登录后10分钟就会被强制登出，需要重新登录。\n\n问题描述：\n1. 用户正常登录后，大约10分钟内会被强制登出\n2. 此时 Token 应该还在有效期内（设置为30分钟）\n3. 问题在高并发时更容易出现\n\n预期效果：\n用户登录后应保持30分钟的会话有效期，除非手动登出。',
  source: 'BUG-2024-001',
  type: 'bug',
  priority: 'high',
  status: 'coding',
  assignee: '张三',
  created_by: 'admin',
  analysis_result: {
    type: 'bug',
    priority: 'high',
    keywords: ['登录', '超时', '登出', 'Token', '会话'],
    confidence: 0.92,
  },
  created_at: '2024-03-15T10:30:00Z',
  updated_at: '2024-03-16T14:20:00Z',
}

const mockHistory: StatusHistoryItem[] = [
  {
    status: 'pending',
    changed_at: '2024-03-15T10:30:00Z',
    changed_by: 'admin',
    comment: '需求已创建',
  },
  {
    status: 'analyzing',
    changed_at: '2024-03-15T11:00:00Z',
    changed_by: 'system',
    comment: 'AI 分析完成，识别为高优先级 Bug',
  },
  {
    status: 'reviewing',
    changed_at: '2024-03-15T14:30:00Z',
    changed_by: 'pm',
    comment: '分析结果已确认，待分配开发人员',
  },
  {
    status: 'coding',
    changed_at: '2024-03-16T09:00:00Z',
    changed_by: '张三',
    comment: '已开始修复，预计今天完成',
  },
]

const mockTeamMembers = ['张三', '李四', '王五', '赵六', '孙七']

export default function RequirementDetail() {
  const { reqId } = useParams<{ reqId: string }>()
  const navigate = useNavigate()
  const [requirement, setRequirement] = useState<Requirement | null>(null)
  const [history, setHistory] = useState<StatusHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)

  useEffect(() => {
    if (reqId) {
      loadRequirement(reqId)
    }
  }, [reqId])

  const loadRequirement = async (id: string) => {
    setIsLoading(true)
    try {
      const [req, hist] = await Promise.all([
        requirementService.getRequirement(id),
        requirementService.getStatusHistory(id),
      ])
      setRequirement(req)
      setHistory(hist)
    } catch {
      console.log('Using mock data')
      setRequirement(mockRequirement)
      setHistory(mockHistory)
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdateStatus = async (newStatus: RequirementStatus, comment?: string) => {
    if (!reqId || !requirement) return
    setIsUpdatingStatus(true)
    try {
      const updated = await requirementService.updateStatus(reqId, newStatus, comment)
      setRequirement(updated)
      setHistory((prev) => [
        ...prev,
        {
          status: newStatus,
          changed_at: new Date().toISOString(),
          changed_by: 'current_user',
          comment,
        },
      ])
    } catch {
      setRequirement((prev) => prev ? { ...prev, status: newStatus } : null)
      setHistory((prev) => [
        ...prev,
        {
          status: newStatus,
          changed_at: new Date().toISOString(),
          changed_by: 'current_user',
          comment,
        },
      ])
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
    } catch {
      setRequirement((prev) => prev ? { ...prev, assignee } : null)
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {requirement.analysis_result && (
            <div>
              <AnalysisCard analysis={requirement.analysis_result} />
            </div>
          )}

          <StatusTimeline history={history} currentStatus={requirement.status} />
        </div>
      </div>

      {showAssignModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">分配负责人</h3>
            <div className="space-y-2">
              {mockTeamMembers.map((member) => (
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
                    onClick={() => handleUpdateStatus(status)}
                    disabled={isUpdatingStatus}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                      requirement.status === status
                        ? 'bg-primary-light border-2 border-primary'
                        : 'bg-gray-50 hover:bg-gray-100'
                    } disabled:opacity-50`}
                  >
                    <span className={`w-2 h-2 rounded-full ${config.dotColor}`} />
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
