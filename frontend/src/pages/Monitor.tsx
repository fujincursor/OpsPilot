import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { projectService, testService } from '../services'
import type { Project } from '../types'

interface WorkflowItem {
  requirement_id: string
  title: string
  type: string
  status: string
  stage: string
  priority: string
  created_by: string
  created_at?: string | null
  updated_at?: string | null
  current_agent?: string
  codegen_task_id?: string | null
  codegen_status?: string
  rework_count?: number
  failure_reason?: string
}

interface WorkflowBoard {
  items: WorkflowItem[]
}

const steps = ['分析', '方案', '方案审批', '编码', '代码审批', '测试', '测试审批', '完成']
const runningStages = new Set(['分析', '方案', '编码', '测试'])
const reviewStages = new Set(['待审批', '方案审批', '代码审批', '测试审批'])

function stepIndex(stage: string): number {
  if (stage === '待审批') return steps.indexOf('方案审批')
  if (stage === '已暂停') return 0
  const index = steps.indexOf(stage)
  return index === -1 ? 0 : index
}

function isToday(value?: string | null): boolean {
  if (!value) return false
  const date = new Date(value)
  const now = new Date()
  return date.getFullYear() === now.getFullYear()
    && date.getMonth() === now.getMonth()
    && date.getDate() === now.getDate()
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

function typeLabel(type: string): string {
  if (type === 'bug') return 'Bug'
  if (type === 'question') return '咨询'
  return '需求'
}

function badge(item: WorkflowItem): { text: string; className: string } {
  if (item.codegen_status === 'failed' || item.failure_reason) {
    return { text: '失败', className: 'bg-red-50 text-red-600' }
  }
  if (reviewStages.has(item.stage)) return { text: '等待审批', className: 'bg-amber-50 text-amber-700' }
  if (item.stage === '完成') return { text: '已完成', className: 'bg-green-50 text-green-700' }
  if (item.stage === '已关闭') return { text: '已关闭', className: 'bg-gray-100 text-gray-500' }
  if (item.stage === '已暂停') return { text: '已暂停', className: 'bg-gray-100 text-gray-600' }
  return { text: '执行中', className: 'bg-blue-50 text-blue-600' }
}

export default function Monitor() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [projectId, setProjectId] = useState(localStorage.getItem('opspilot.currentProjectId') || '')
  const [items, setItems] = useState<WorkflowItem[]>([])
  const [error, setError] = useState('')
  const [testTaskIds, setTestTaskIds] = useState<Record<string, string>>({})
  const [online, setOnline] = useState(true)
  const projectRef = useRef(projectId)
  projectRef.current = projectId

  const load = (id = projectId) => {
    api.get<{ available: boolean }>('/deerflow/status')
      .then((response) => setOnline(response.data.available))
      .catch(() => setOnline(false))
    if (!id) {
      setItems([])
      setError('请先选择项目')
      return
    }
    setError('')
    api.get<WorkflowBoard>(`/projects/${id}/workflow`)
      .then((response) => {
        const next = response.data.items || []
        setItems(next)
        const coded = next.filter((item) => item.codegen_task_id)
        Promise.all(coded.map(async (item) => {
          const tasks = await testService.getTasksByCodegen(item.codegen_task_id as string).catch(() => [])
          return tasks[0] ? [item.codegen_task_id as string, tasks[0].id] as const : null
        })).then((pairs) => {
          const map: Record<string, string> = {}
          pairs.forEach((pair) => {
            if (pair) map[pair[0]] = pair[1]
          })
          setTestTaskIds(map)
        })
      })
      .catch(() => {
        setItems([])
        setError('监控数据加载失败')
      })
  }

  useEffect(() => {
    projectService.getProjects().then((loaded) => {
      setProjects(loaded)
      const saved = localStorage.getItem('opspilot.currentProjectId')
      const current = loaded.find((item) => item.id === saved) || loaded[0]
      if (!current) return
      setProjectId(current.id)
      localStorage.setItem('opspilot.currentProjectId', current.id)
      load(current.id)
    }).catch(() => setError('项目列表加载失败'))
    const timer = window.setInterval(() => load(projectRef.current), 30000)
    return () => window.clearInterval(timer)
  }, [])

  const chooseProject = (id: string) => {
    const project = projects.find((item) => item.id === id)
    setProjectId(id)
    localStorage.setItem('opspilot.currentProjectId', id)
    if (project) window.dispatchEvent(new CustomEvent('opspilot-project', { detail: project }))
    load(id)
  }

  const active = items.filter((item) => runningStages.has(item.stage) || reviewStages.has(item.stage))
  const history = items.filter((item) => !active.includes(item))
  const running = items.filter((item) => runningStages.has(item.stage) && item.codegen_status !== 'failed' && !item.failure_reason)
  const waiting = items.filter((item) => reviewStages.has(item.stage))
  const finishedToday = items.filter((item) => item.stage === '完成' && isToday(item.updated_at))
  const failed = items.filter((item) => item.codegen_status === 'failed' || item.failure_reason)
  const retrying = items.filter((item) => (item.rework_count || 0) > 0 && item.stage !== '完成' && item.stage !== '已关闭')
  const count = (list: WorkflowItem[], type: string) => list.filter((item) => item.type === type).length

  const cards = [
    {
      label: '执行中',
      value: running.length,
      detail: `Bug修复: ${count(running, 'bug')} · 需求: ${count(running, 'feature')}`,
      icon: 'bg-blue-50 text-blue-500',
      mark: '▮▮▮',
    },
    {
      label: '等待审批',
      value: waiting.length,
      detail: `方案审批: ${waiting.filter((item) => item.stage === '方案审批' || item.stage === '待审批').length} · 代码审批: ${waiting.filter((item) => item.stage === '代码审批').length} · 测试审批: ${waiting.filter((item) => item.stage === '测试审批').length}`,
      icon: 'bg-amber-50 text-amber-500',
      mark: '❚❚',
    },
    {
      label: '今日完成',
      value: finishedToday.length,
      detail: `Bug: ${count(finishedToday, 'bug')} · 需求: ${count(finishedToday, 'feature')}`,
      icon: 'bg-green-50 text-green-500',
      mark: '✓',
    },
    {
      label: '失败',
      value: failed.length,
      detail: `重试中: ${retrying.length}`,
      icon: 'bg-red-50 text-red-500',
      mark: '✕',
    },
  ]

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold text-gray-900">Agent 执行监控</h1>
          <div className="flex items-center gap-3">
            <span className={`hidden text-sm sm:inline ${online ? 'text-green-600' : 'text-red-500'}`}>
              {online ? '系统正常' : '系统离线'}
            </span>
            <select
              value={projectId}
              onChange={(event) => chooseProject(event.target.value)}
              className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700"
            >
              {projects.length === 0 && <option value="">暂无项目</option>}
              {projects.map((project) => (
                <option key={project.id} value={project.id}>{project.name}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => load()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              刷新
            </button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <div key={card.label} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className={`mb-4 flex h-8 w-8 items-center justify-center rounded-lg text-sm font-semibold ${card.icon}`}>
                {card.mark}
              </div>
              <div className="text-3xl font-semibold text-gray-900">{card.value}</div>
              <div className="mt-1 text-sm text-gray-800">{card.label}</div>
              <div className="mt-1 text-xs text-gray-400">{card.detail}</div>
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <section>
          <h2 className="mb-3 text-base font-semibold text-gray-900">当前执行中任务 ({active.length})</h2>
          {active.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-200 bg-white px-4 py-8 text-center text-sm text-gray-400">
              当前没有正在执行的任务
            </div>
          ) : (
            <div className="space-y-4">
              {active.map((item) => (
                <TaskCard
                  key={item.requirement_id}
                  item={item}
                  projectName={projects.find((project) => project.id === projectId)?.name || ''}
                  testTaskId={item.codegen_task_id ? testTaskIds[item.codegen_task_id] : ''}
                  onOpen={() => navigate(`/monitor/${item.requirement_id}`)}
                  onCode={() => item.codegen_task_id && navigate(`/codegen/${item.codegen_task_id}`)}
                  onTest={(id) => navigate(`/tests/${id}`)}
                />
              ))}
            </div>
          )}
        </section>

        {history.length > 0 && (
          <section>
            <h2 className="mb-3 text-base font-semibold text-gray-900">历史工单 ({history.length})</h2>
            <div className="divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white">
              {history.map((item) => {
                const state = badge(item)
                const testId = item.codegen_task_id ? testTaskIds[item.codegen_task_id] : ''
                return (
                  <div key={item.requirement_id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
                    <button type="button" onClick={() => navigate(`/monitor/${item.requirement_id}`)} className="min-w-0 text-left">
                      <span className="block truncate text-sm text-gray-800">{item.title}</span>
                      <span className="mt-1 block text-xs text-gray-400">{typeLabel(item.type)} · {item.stage}</span>
                    </button>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-md px-2 py-1 text-xs ${state.className}`}>{state.text}</span>
                      {item.codegen_task_id && (
                        <button type="button" onClick={() => navigate(`/codegen/${item.codegen_task_id}`)} className="rounded-md bg-blue-600 px-2.5 py-1 text-xs text-white">
                          查看生成代码
                        </button>
                      )}
                      {testId && (
                        <button type="button" onClick={() => navigate(`/tests/${testId}`)} className="rounded-md bg-gray-100 px-2.5 py-1 text-xs text-gray-700">
                          查看测试报告
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

function TaskCard({
  item,
  projectName,
  testTaskId,
  onOpen,
  onCode,
  onTest,
}: {
  item: WorkflowItem
  projectName: string
  testTaskId?: string
  onOpen: () => void
  onCode: () => void
  onTest: (id: string) => void
}) {
  const current = item.stage === '已暂停' || item.stage === '已关闭' ? -1 : stepIndex(item.stage)
  const progress = item.stage === '完成' ? 100 : current < 0 ? 0 : Math.round((current / (steps.length - 1)) * 100)
  const state = badge(item)
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <button type="button" onClick={onOpen} className="min-w-0 text-left">
          <div className="flex items-center gap-2">
            <span>{item.type === 'bug' ? '🐛' : '✨'}</span>
            <span className="truncate text-base font-medium text-gray-900">{item.title}</span>
            <span className="shrink-0 text-xs text-gray-400">{item.requirement_id.slice(0, 8).toUpperCase()}</span>
          </div>
          <p className="mt-1 text-xs text-gray-400">
            {projectName || '当前项目'} · {item.created_by || '未记录提交人'}
          </p>
        </button>
        <span className={`shrink-0 rounded-md px-2 py-1 text-xs ${state.className}`}>{state.text}</span>
      </div>

      <div className="mt-5 text-sm text-gray-500">
        当前阶段: <span className="text-gray-800">{item.stage}</span>
      </div>
      <div className="mt-2 flex items-center gap-2 text-sm text-gray-700">
        <span className="inline-block h-2 w-2 rounded-sm bg-gray-700" />
        {item.current_agent || 'Lead Agent'}
      </div>

      <div className="mt-4 flex gap-3 overflow-x-auto pb-1 text-xs">
        {steps.map((step, index) => {
          const done = item.stage === '完成' || (current >= 0 && index < current)
          const here = current >= 0 && index === current && item.stage !== '完成'
          return (
            <span key={step} className={`shrink-0 ${done ? 'text-green-600' : here ? 'font-medium text-blue-600' : 'text-gray-300'}`}>
              {done ? '✓' : here ? '●' : '○'} {step}
            </span>
          )
        })}
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-100">
        <div className="h-full rounded-full bg-blue-600" style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-400">
        <span>开始: {clock(item.created_at)}</span>
        <span>已执行: {elapsed(item.created_at)}</span>
        <span>{item.stage}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {item.codegen_task_id && (
          <button type="button" onClick={onCode} className="rounded-md bg-blue-600 px-3 py-1.5 text-xs text-white">
            查看生成代码
          </button>
        )}
        {testTaskId && (
          <button type="button" onClick={() => onTest(testTaskId)} className="rounded-md bg-gray-100 px-3 py-1.5 text-xs text-gray-700">
            查看测试报告
          </button>
        )}
      </div>
    </div>
  )
}
