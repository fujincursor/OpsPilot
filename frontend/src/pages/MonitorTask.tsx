import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../services/api'

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
}

interface WorkflowBoard {
  items: WorkflowItem[]
}

const stages = ['分析', '方案', '方案审批', '编码', '代码审批', '测试', '完成']

function activeIndex(stage: string): number {
  if (stage === '分析') return 0
  if (stage === '方案') return 1
  if (stage === '待审批') return 2
  if (stage === '编码') return 3
  if (stage === '测试') return 5
  if (stage === '完成' || stage === '已关闭') return 6
  return 0
}

export default function MonitorTask() {
  const { requirementId } = useParams<{ requirementId: string }>()
  const navigate = useNavigate()
  const [item, setItem] = useState<WorkflowItem | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const projectId = localStorage.getItem('opspilot.currentProjectId')
    if (!projectId || !requirementId) {
      setError('请先选择项目')
      return
    }
    api.get<WorkflowBoard>(`/projects/${projectId}/workflow`)
      .then((response) => {
        const found = response.data.items.find((entry) => entry.requirement_id === requirementId) || null
        setItem(found)
        if (!found) setError('没有找到这条流程')
      })
      .catch(() => setError('流程数据加载失败'))
  }, [requirementId])

  const current = item ? activeIndex(item.stage) : 0
  const logs = item
    ? [
        `需求「${item.title}」当前阶段：${item.stage}`,
        `执行 Agent：${item.current_agent || 'Lead Agent'}`,
        item.stage === '待审批' || item.stage === '方案' ? '节点标记：等待人工审批（HITL）' : '节点标记：自动阶段',
        item.auto_advance ? '自动推进：开启' : '自动推进：已暂停',
        item.sandbox_profile ? `执行环境：${item.sandbox_profile}` : '执行环境：未配置',
        'Token / API 消耗：未采集',
      ]
    : []

  return (
    <div className="p-6 space-y-6">
      <button type="button" onClick={() => navigate('/monitor')} className="text-sm text-gray-600">
        ← 返回监控
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {item && (
        <>
          <div>
            <h1 className="text-2xl font-semibold text-gray-800">{item.title}</h1>
            <p className="mt-1 text-sm text-gray-500">{item.type} · {item.status} · {item.stage}</p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="mb-4 text-sm font-semibold text-gray-700">执行流程</h2>
            <div className="flex flex-wrap gap-2">
              {stages.map((stage, index) => {
                const hitl = stage.includes('审批')
                const state = index < current ? 'done' : index === current ? 'current' : 'pending'
                return (
                  <div
                    key={stage}
                    className={`rounded-lg border px-3 py-2 text-xs ${
                      state === 'current' ? 'border-primary bg-primary/10 text-primary' : state === 'done' ? 'border-green-200 bg-green-50 text-green-700' : 'border-gray-200 text-gray-400'
                    }`}
                  >
                    {stage}{hitl ? ' · HITL' : ''}
                  </div>
                )
              })}
            </div>
          </div>
          <div className="rounded-xl bg-gray-900 p-4 font-mono text-xs text-green-300">
            {logs.map((line) => (
              <div key={line}>$ {line}</div>
            ))}
          </div>
          {item.session_id && (
            <button type="button" onClick={() => navigate(`/chat/${item.session_id}`)} className="rounded-md bg-primary px-3 py-2 text-sm text-white">
              查看对话
            </button>
          )}
        </>
      )}
    </div>
  )
}
