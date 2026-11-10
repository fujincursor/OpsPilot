import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyticsService, projectService, reviewService } from '../services'
import type { GlobalStats } from '../services/analyticsService'
import { authService } from '../services/authService'

interface Activity {
  id: string
  action: string
  target: string
  time: string
  icon: string
}

function formatTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function Home() {
  const navigate = useNavigate()
  const user = authService.getUser()
  const [stats, setStats] = useState<GlobalStats | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [projectId, setProjectId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'flow' | 'modules'>('flow')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const [globalStats, projects, reviews] = await Promise.all([
          analyticsService.getGlobalStats(),
          projectService.getProjects(),
          reviewService.getPendingReviews(),
        ])
        setStats(globalStats)
        setProjectId(projects[0]?.id ?? null)
        const projectActivities: Activity[] = projects.slice(0, 4).map((project) => ({
          id: `project-${project.id}`,
          action: '项目',
          target: project.name,
          time: formatTime(project.updated_at || project.created_at),
          icon: '📁',
        }))
        const reviewActivities: Activity[] = reviews.slice(0, 4).map((review) => ({
          id: `review-${review.id}`,
          action: '待审核',
          target: review.title,
          time: formatTime(review.created_at),
          icon: '👀',
        }))
        setActivities([...reviewActivities, ...projectActivities].slice(0, 6))
      } catch (loadError) {
        console.error(loadError)
        setError('工作台数据加载失败')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const cards = stats
    ? [
        { title: '项目总数', value: stats.total_projects, icon: '📁' },
        { title: '需求总数', value: stats.total_requirements, icon: '📋' },
        { title: '已完成', value: stats.total_completed, icon: '✅' },
        { title: '启用中的 Agent', value: stats.active_agents, icon: '🤖' },
      ]
    : []

  const flowSteps = [
    '知识库与项目资料已就绪？',
    '需求输入 → 分析分类（Bug / 新需求 / 咨询）',
    '方案设计',
    '人工 Review 通过？',
    '代码生成 → 语法检查',
    '代码 Review',
    '测试执行 → 质量门禁',
    '知识回写 → 完成',
  ]
  const modules = [
    { id: 'M1', title: '多项目与 Agent', description: '项目、成员、Prompt 和工具链', path: '/projects' },
    { id: 'M2', title: '项目信息', description: '概述、架构、目录和 Runbook', path: projectId ? `/projects/${projectId}/profile` : '/projects' },
    { id: 'M3', title: '知识库', description: '文档、代码索引和检索', path: projectId ? `/projects/${projectId}/knowledge` : '/projects' },
    { id: 'M4', title: '需求理解', description: '提交并分类 Bug、新需求和咨询', path: projectId ? `/projects/${projectId}/requirements` : '/projects' },
    { id: 'M5', title: 'Bug 修复', description: '在需求列表中筛选 Bug', path: projectId ? `/projects/${projectId}/requirements` : '/projects' },
    { id: 'M6', title: '新需求设计', description: '在需求列表中筛选新需求', path: projectId ? `/projects/${projectId}/requirements` : '/projects' },
    { id: 'M7', title: '人工 Review', description: '方案和代码审批', path: '/reviews' },
    { id: 'M8', title: '代码生成', description: '从已通过的方案进入编码', path: '/monitor' },
    { id: 'M9', title: '测试执行', description: '从代码任务进入测试报告', path: '/monitor' },
  ]

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-gray-800 mb-2">
            欢迎回来，{user?.username || '用户'}
          </h1>
          <p className="text-gray-500">
            {stats
              ? `完成率 ${stats.avg_completion_rate}% ，当前有 ${stats.active_agents} 个启用中的 Agent。`
              : '正在读取工作台数据。'}
          </p>
        </div>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm animate-pulse h-28" />
              ))
            : cards.map((stat) => (
                <div key={stat.title} className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
                  <div className="text-2xl mb-3">{stat.icon}</div>
                  <div className="text-2xl font-semibold text-gray-800 mb-1">{stat.value}</div>
                  <div className="text-sm text-gray-500">{stat.title}</div>
                </div>
              ))}
        </div>

        <div className="mb-4 flex gap-2">
          <button
            type="button"
            onClick={() => setTab('flow')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === 'flow' ? 'bg-primary text-white' : 'bg-white text-gray-600 border border-gray-200'}`}
          >
            整体业务流程
          </button>
          <button
            type="button"
            onClick={() => setTab('modules')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === 'modules' ? 'bg-primary text-white' : 'bg-white text-gray-600 border border-gray-200'}`}
          >
            功能模块
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            {tab === 'flow' ? (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex flex-col items-start gap-2">
                  {flowSteps.map((step, index) => (
                    <div key={step} className="w-full">
                      <div className={`rounded-lg border px-4 py-3 text-sm text-gray-800 ${index % 3 === 0 ? 'border-amber-200 bg-amber-50' : 'border-gray-200'}`}>
                        {step}
                      </div>
                      {index < flowSteps.length - 1 && <div className="ml-6 h-4 border-l border-gray-300" />}
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs text-gray-400">未通过的环节会退回上一阶段；咨询只回答，不进入编码。</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {modules.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => navigate(item.path)}
                    className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm text-left hover:border-primary hover:shadow-md transition-all"
                  >
                    <div className="text-xs font-semibold text-primary mb-2">{item.id}</div>
                    <div className="text-base font-semibold text-gray-800 mb-1">{item.title}</div>
                    <div className="text-sm text-gray-500">{item.description}</div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-4">最近活动</h2>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              {activities.length === 0 ? (
                <p className="p-6 text-sm text-gray-400 text-center">暂无活动</p>
              ) : (
                activities.map((activity, index) => (
                  <div
                    key={activity.id}
                    className={`p-4 flex items-start gap-3 ${
                      index !== activities.length - 1 ? 'border-b border-gray-100' : ''
                    }`}
                  >
                    <span className="text-lg">{activity.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-gray-800">{activity.action}</div>
                      <div className="text-xs text-gray-500 mt-0.5 truncate">{activity.target}</div>
                    </div>
                    <div className="text-xs text-gray-400 whitespace-nowrap">{activity.time}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
