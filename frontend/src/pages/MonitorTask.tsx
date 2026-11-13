import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../services/api'
import { testService } from '../services'

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
  created_at?: string | null
  created_by?: string
  priority?: string
  current_agent?: string
  codegen_task_id?: string | null
  codegen_status?: string
  codegen_error?: string
  codegen_files?: string[]
  code_review_id?: string | null
  rework_count?: number
  failure_reason?: string
}

interface WorkflowBoard {
  items: WorkflowItem[]
}

const steps = [
  { key: '分析', title: 'Lead Agent', icon: '🤖' },
  { key: '方案', title: '方案 Agent', icon: '🔧' },
  { key: '方案审批', title: 'HITL 方案审批', icon: '⏸', hitl: true },
  { key: '编码', title: 'Code Gen Agent', icon: '💻' },
  { key: '代码审批', title: 'HITL 代码审批', icon: '⏸', hitl: true },
  { key: '测试', title: 'Test Agent', icon: '🧪' },
  { key: '测试审批', title: 'HITL 测试审批', icon: '⏸', hitl: true },
  { key: '完成', title: '完成', icon: '✓' },
]

function stepIndex(stage: string): number {
  if (stage === '待审批') return 2
  if (stage === '已暂停' || stage === '已关闭') return 0
  const index = steps.findIndex((step) => step.key === stage)
  return index === -1 ? 0 : index
}

function elapsed(from?: string | null): string {
  if (!from) return '—'
  const minutes = Math.floor((Date.now() - new Date(from).getTime()) / 60000)
  if (!Number.isFinite(minutes) || minutes < 0) return '—'
  if (minutes < 1) return '不到 1 分钟'
  if (minutes < 60) return `${minutes} 分钟`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest ? `${hours} 小时 ${rest} 分钟` : `${hours} 小时`
}

function clock(value?: string | null): string {
  if (!value) return '—'
  return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const priorityText: Record<string, { label: string; dot: string }> = {
  low: { label: '低', dot: 'bg-gray-400' },
  medium: { label: '中', dot: 'bg-amber-400' },
  high: { label: '高', dot: 'bg-red-500' },
  critical: { label: '紧急', dot: 'bg-red-600' },
}

export default function MonitorTask() {
  const { requirementId } = useParams<{ requirementId: string }>()
  const navigate = useNavigate()
  const flowRef = useRef<HTMLDivElement>(null)
  const [item, setItem] = useState<WorkflowItem | null>(null)
  const [error, setError] = useState('')
  const [testTaskId, setTestTaskId] = useState('')

  const load = () => {
    const projectId = localStorage.getItem('opspilot.currentProjectId')
    if (!projectId || !requirementId) {
      setError('请先选择项目')
      return
    }
    api.get<WorkflowBoard>(`/projects/${projectId}/workflow`)
      .then((response) => {
        const found = response.data.items.find((entry) => entry.requirement_id === requirementId) || null
        setItem(found)
        setError(found ? '' : '没有找到这条流程')
        if (found?.codegen_task_id) {
          testService.getTasksByCodegen(found.codegen_task_id)
            .then((tasks) => setTestTaskId(tasks[0]?.id || ''))
            .catch(() => setTestTaskId(''))
        } else {
          setTestTaskId('')
        }
      })
      .catch(() => setError('流程数据加载失败'))
  }

  useEffect(() => {
    load()
    const timer = window.setInterval(load, 5000)
    return () => window.clearInterval(timer)
  }, [requirementId])

  const current = !item || item.stage === '已暂停' || item.stage === '已关闭' ? -1 : stepIndex(item.stage)
  const finished = item?.stage === '完成'
  const stateText = !item ? ''
    : item.codegen_status === 'failed' || item.failure_reason ? '失败'
    : item.stage.includes('审批') || item.stage === '待审批' ? '等待审批'
    : item.stage === '完成' ? '已完成'
    : item.stage === '已关闭' ? '已关闭'
    : item.stage === '已暂停' ? '已暂停'
    : '执行中'
  const priority = priorityText[item?.priority || 'medium'] || priorityText.medium
  const solutionAgent = item?.type === 'bug' ? 'Bug Fix Agent' : item?.type === 'question' ? 'Lead Agent' : 'Feature Design Agent'

  const fullscreen = () => {
    const node = flowRef.current
    if (!node) return
    if (document.fullscreenElement) document.exitFullscreen()
    else node.requestFullscreen().catch(() => undefined)
  }

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => navigate('/monitor')} className="text-sm text-gray-500 hover:text-gray-800">
            ← 返回监控列表
          </button>
          {item && (
            <>
              <span className="text-lg">{item.type === 'bug' ? '🐛' : '✨'}</span>
              <h1 className="text-xl font-semibold text-gray-900">
                {item.requirement_id.slice(0, 8).toUpperCase()} · {item.title}
              </h1>
              <span className={`rounded-md px-2 py-1 text-xs ${stateText === '执行中' ? 'bg-blue-50 text-blue-600' : stateText === '失败' ? 'bg-red-50 text-red-600' : stateText === '已完成' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
                {stateText}
              </span>
            </>
          )}
        </div>
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
        {item && (
          <div className="grid items-start gap-4 lg:grid-cols-[320px_1fr]">
            <div ref={flowRef} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-800">执行流程</h2>
                <div className="flex gap-2">
                  <button type="button" onClick={fullscreen} className="rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600">全屏</button>
                  <button type="button" onClick={load} className="rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-600">刷新</button>
                </div>
              </div>
              <div className="space-y-0">
                {steps.map((step, index) => {
                  const done = finished || (current >= 0 && index < current)
                  const here = current >= 0 && !finished && index === current
                  const title = step.key === '方案' ? solutionAgent : here && item.current_agent ? item.current_agent : step.title
                  const note = done && step.hitl ? '已通过' : done ? '已完成' : here && step.hitl ? '等待审批' : here ? '执行中' : '等待'
                  const border = here
                    ? 'border-blue-400 bg-blue-50 shadow-sm'
                    : done && step.hitl
                      ? 'border-dashed border-green-400 bg-green-50/60'
                      : done
                        ? 'border-green-400 bg-green-50/40'
                        : 'border-gray-200 bg-white text-gray-400'
                  return (
                    <div key={step.key}>
                      <div className={`rounded-xl border px-4 py-4 text-center ${border}`}>
                        <div className="text-lg">{step.icon}</div>
                        <div className={`mt-1 text-sm font-medium ${here ? 'text-blue-700' : done ? 'text-gray-800' : 'text-gray-400'}`}>{title}</div>
                        <div className={`mt-1 text-xs ${done ? 'text-green-600' : here ? 'text-blue-500' : 'text-gray-300'}`}>
                          {done || here ? `${done ? '✓' : '●'} ${note}` : note}
                        </div>
                      </div>
                      {index < steps.length - 1 && (
                        <div className={`mx-auto h-6 w-px ${done ? 'bg-green-300' : 'bg-gray-200'}`} />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 text-sm font-semibold text-gray-800">任务信息</h2>
                <dl className="divide-y divide-gray-100 text-sm">
                  <Row label="工单编号" value={item.requirement_id.slice(0, 8).toUpperCase()} />
                  <Row label="工单类型" value={item.type === 'bug' ? 'Bug' : item.type === 'question' ? '咨询' : '需求'} />
                  <Row label="优先级" value={<span className="inline-flex items-center gap-2">{priority.label}<span className={`h-2.5 w-2.5 rounded-full ${priority.dot}`} /></span>} />
                  <Row label="提交人" value={item.created_by || '—'} />
                  <Row label="开始时间" value={clock(item.created_at)} />
                  <Row label="已执行" value={elapsed(item.created_at)} />
                  <Row label="当前阶段" value={item.stage} />
                  <Row label="自动推进" value={item.auto_advance ? '开启' : '已暂停'} />
                </dl>
                {(item.codegen_error || item.failure_reason) && (
                  <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-xs text-red-600">{item.codegen_error || item.failure_reason}</p>
                )}
                <div className="mt-4 flex flex-wrap gap-2">
                  {item.codegen_task_id && (
                    <button type="button" onClick={() => navigate(`/codegen/${item.codegen_task_id}`)} className="rounded-md bg-blue-600 px-3 py-1.5 text-xs text-white">查看生成代码</button>
                  )}
                  {testTaskId && (
                    <button type="button" onClick={() => navigate(`/tests/${testTaskId}`)} className="rounded-md bg-gray-100 px-3 py-1.5 text-xs text-gray-700">查看测试报告</button>
                  )}
                  {item.code_review_id && (
                    <button type="button" onClick={() => navigate(`/reviews/${item.code_review_id}`)} className="rounded-md bg-gray-100 px-3 py-1.5 text-xs text-gray-700">去审批代码</button>
                  )}
                  {item.session_id && (
                    <button type="button" onClick={() => navigate(`/chat/${item.session_id}`)} className="rounded-md bg-gray-100 px-3 py-1.5 text-xs text-gray-700">查看对话</button>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 text-sm font-semibold text-gray-800">资源消耗</h2>
                <dl className="divide-y divide-gray-100 text-sm">
                  <Row label="Token 消耗" value="未采集" />
                  <Row label="预估成本" value="未采集" />
                  <Row label="API 调用" value="未采集" />
                  <Row label="知识引用" value="未采集" />
                  <Row label="重试次数" value={String(item.rework_count || 0)} />
                  <Row label="执行环境" value={item.sandbox_profile || '未配置'} />
                </dl>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <dt className="text-gray-500">{label}</dt>
      <dd className="max-w-[60%] break-all text-right text-gray-800">{value}</dd>
    </div>
  )
}
