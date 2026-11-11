import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

interface AgentStatus {
  available: boolean
}

interface WorkflowItem {
  requirement_id: string
  title: string
  type: string
  status: string
  stage: string
  auto_advance: boolean
  session_id?: string | null
  sandbox_profile: string
  updated_at?: string | null
  current_agent?: string
  codegen_task_id?: string | null
  codegen_status?: string
  codegen_error?: string
  codegen_files?: string[]
  code_review_id?: string | null
}

interface WorkflowBoard {
  running: number
  pending_review: number
  completed: number
  closed: number
  items: WorkflowItem[]
}

export default function Monitor() {
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'ready' | 'offline'>('loading')
  const [board, setBoard] = useState<WorkflowBoard | null>(null)
  const [error, setError] = useState('')
  const [actingId, setActingId] = useState('')

  const load = () => {
    const projectId = localStorage.getItem('opspilot.currentProjectId')
    setStatus('loading')
    api.get<AgentStatus>('/deerflow/status')
      .then((response) => setStatus(response.data.available ? 'ready' : 'offline'))
      .catch(() => setStatus('offline'))
    if (!projectId) {
      setBoard(null)
      setError('请先选择项目')
      return
    }
    setError('')
    api.get<WorkflowBoard>(`/projects/${projectId}/workflow`)
      .then((response) => setBoard(response.data))
      .catch(() => {
        setBoard(null)
        setError('流程数据加载失败')
      })
  }

  useEffect(() => {
    load()
  }, [])

  const act = async (item: WorkflowItem, action: 'pause' | 'resume' | 'stop') => {
    setActingId(item.requirement_id)
    try {
      await api.post(`/requirements/${item.requirement_id}/workflow/${action}`)
      load()
    } catch {
      setError('操作失败')
    } finally {
      setActingId('')
    }
  }

  const today = new Date().toDateString()
  const updatedToday = (value?: string | null) => {
    if (!value) return false
    const date = new Date(value)
    return !Number.isNaN(date.getTime()) && date.toDateString() === today
  }
  const cards = [
    { label: '执行中', value: board?.running ?? 0 },
    { label: '等待审批', value: board?.pending_review ?? 0 },
    { label: '今日完成', value: (board?.items || []).filter((item) => item.stage === '完成' && updatedToday(item.updated_at)).length },
    { label: '今日终止', value: (board?.items || []).filter((item) => item.stage === '已关闭' && updatedToday(item.updated_at)).length },
  ]
  const progressOf = (stage: string) => {
    const table: Record<string, number> = {
      分析: 15, 方案: 35, 待审批: 50, 编码: 70, 代码审批: 80, 测试: 90, 完成: 100, 已关闭: 100, 已暂停: 40,
    }
    return table[stage] ?? 10
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">执行监控</h1>
          <p className="text-sm text-gray-500 mt-1">
            Agent {status === 'ready' ? '就绪' : status === 'offline' ? '离线' : '检测中'}
          </p>
        </div>
        <button
          onClick={load}
          className="px-3 py-2 rounded-md text-sm font-medium bg-primary text-white"
        >
          刷新
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-semibold text-gray-800">{card.value}</div>
            <div className="text-sm text-gray-500">{card.label}</div>
          </div>
        ))}
      </div>

      {error && <div className="text-sm text-red-500">{error}</div>}

      <div className="space-y-3">
        {(board?.items || []).map((item) => (
          <div key={item.requirement_id} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-medium text-gray-800">{item.title}</div>
                <div className="mt-1 text-xs text-gray-500">
                  {item.type} · {item.stage} · {item.status}
                  {item.auto_advance ? '' : ' · 自动推进已暂停'}
                </div>
                <div className="mt-2 h-1.5 w-48 overflow-hidden rounded-full bg-gray-100">
                  <div className="h-full bg-primary" style={{ width: `${progressOf(item.stage)}%` }} />
                </div>
                <div className="mt-1 text-xs text-gray-400">
                  当前 Agent：{item.current_agent || 'Lead Agent'} · 消耗：未采集
                  {item.sandbox_profile ? ` · 环境：${item.sandbox_profile}` : ''}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => navigate(`/monitor/${item.requirement_id}`)}
                  className="px-2.5 py-1 text-xs rounded-md bg-primary text-white"
                >
                  任务详情
                </button>
                {item.session_id && (
                  <button
                    type="button"
                    onClick={() => navigate(`/chat/${item.session_id}`)}
                    className="px-2.5 py-1 text-xs rounded-md bg-gray-100 text-gray-700"
                  >
                    查看对话
                  </button>
                )}
                {item.auto_advance ? (
                  <button
                    type="button"
                    disabled={actingId === item.requirement_id || item.stage === '完成' || item.stage === '已关闭'}
                    onClick={() => act(item, 'pause')}
                    className="px-2.5 py-1 text-xs rounded-md bg-amber-100 text-amber-700 disabled:opacity-40"
                  >
                    暂停
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={actingId === item.requirement_id || item.stage === '已关闭'}
                    onClick={() => act(item, 'resume')}
                    className="px-2.5 py-1 text-xs rounded-md bg-green-100 text-green-700 disabled:opacity-40"
                  >
                    恢复
                  </button>
                )}
                <button
                  type="button"
                  disabled={actingId === item.requirement_id || item.stage === '已关闭'}
                  onClick={() => act(item, 'stop')}
                  className="px-2.5 py-1 text-xs rounded-md bg-red-50 text-red-600 disabled:opacity-40"
                >
                  终止
                </button>
              </div>
            </div>
          </div>
        ))}
        {board && board.items.length === 0 && (
          <div className="text-sm text-gray-500">当前项目还没有需求流程。</div>
        )}
      </div>
    </div>
  )
}
