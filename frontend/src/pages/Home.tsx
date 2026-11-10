import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyticsService } from '../services'
import type { DashboardStats } from '../types'

interface StatCard {
  title: string
  value: string | number
  change?: string
  changeType?: 'up' | 'down' | 'neutral'
  icon: string
}

interface QuickLink {
  title: string
  description: string
  icon: string
  path: string
}

const defaultStats: StatCard[] = [
  { title: '待处理工单', value: 12, change: '+3', changeType: 'up', icon: '📋' },
  { title: '进行中任务', value: 5, icon: '⚡' },
  { title: '今日完成', value: 8, change: '+2', changeType: 'up', icon: '✅' },
  { title: 'Agent 可用率', value: '99.9%', icon: '🤖' },
]

const quickLinks: QuickLink[] = [
  {
    title: '开始对话',
    description: '与智能运维助手交流',
    icon: '💬',
    path: '/chat',
  },
  {
    title: '项目管理',
    description: '查看和管理项目',
    icon: '📁',
    path: '/projects',
  },
  {
    title: '运营看板',
    description: '查看运营数据分析',
    icon: '📊',
    path: '/projects/default/dashboard',
  },
  {
    title: '知识库',
    description: '浏览项目知识文档',
    icon: '📚',
    path: '/knowledge',
  },
]

const recentActivities = [
  {
    id: 1,
    action: 'Bug 修复完成',
    target: 'BUG-2024-001',
    time: '10 分钟前',
    icon: '🐛',
  },
  {
    id: 2,
    action: '新需求已创建',
    target: 'FEAT-2024-004',
    time: '30 分钟前',
    icon: '✨',
  },
  {
    id: 3,
    action: 'HITL 审批通过',
    target: 'BUG-2024-002',
    time: '1 小时前',
    icon: '✅',
  },
  {
    id: 4,
    action: '知识库已更新',
    target: '项目架构说明.md',
    time: '2 小时前',
    icon: '📄',
  },
]

export default function Home() {
  const navigate = useNavigate()
  const [, setGlobalStats] = useState<DashboardStats | null>(null)
  const [stats, setStats] = useState<StatCard[]>(defaultStats)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadGlobalStats()
  }, [])

  const loadGlobalStats = async () => {
    try {
      const data = await analyticsService.getGlobalStats()
      setGlobalStats(data)
      setStats([
        { 
          title: '总需求数', 
          value: data.total_requirements, 
          change: '+12%', 
          changeType: 'up', 
          icon: '📋' 
        },
        { 
          title: '进行中任务', 
          value: data.in_progress, 
          icon: '⚡' 
        },
        { 
          title: '已完成', 
          value: data.completed, 
          change: '+8%', 
          changeType: 'up', 
          icon: '✅' 
        },
        { 
          title: '待审核', 
          value: data.pending_review, 
          change: '-5%', 
          changeType: 'down', 
          icon: '👀' 
        },
      ])
    } catch (error) {
      console.error('Failed to load global stats:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-gray-800 mb-2">
            欢迎回来，张三 👋
          </h1>
          <p className="text-gray-500">
            这是您的运维工作台，所有 Agent 服务运行正常。
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {loading ? (
            Array(4).fill(0).map((_, i) => (
              <div key={i} className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm animate-pulse">
                <div className="h-8 w-8 bg-gray-200 rounded mb-3"></div>
                <div className="h-8 w-20 bg-gray-200 rounded mb-1"></div>
                <div className="h-4 w-24 bg-gray-100 rounded"></div>
              </div>
            ))
          ) : stats.map((stat) => (
            <div
              key={stat.title}
              className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{stat.icon}</span>
                {stat.change && (
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded ${
                      stat.changeType === 'up'
                        ? 'bg-green-100 text-green-600'
                        : stat.changeType === 'down'
                        ? 'bg-red-100 text-red-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {stat.change}
                  </span>
                )}
              </div>
              <div className="text-2xl font-semibold text-gray-800 mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-gray-500">{stat.title}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Links */}
          <div className="lg:col-span-2">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">快捷入口</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {quickLinks.map((link) => (
                <button
                  key={link.title}
                  onClick={() => navigate(link.path)}
                  className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm text-left hover:border-primary hover:shadow-md transition-all group"
                >
                  <div className="text-3xl mb-3 group-hover:scale-110 transition-transform">
                    {link.icon}
                  </div>
                  <div className="text-base font-semibold text-gray-800 mb-1">
                    {link.title}
                  </div>
                  <div className="text-sm text-gray-500">{link.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Recent Activities */}
          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-4">最近活动</h2>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              {recentActivities.map((activity, index) => (
                <div
                  key={activity.id}
                  className={`p-4 flex items-start gap-3 ${
                    index !== recentActivities.length - 1 ? 'border-b border-gray-100' : ''
                  }`}
                >
                  <span className="text-lg">{activity.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-800">{activity.action}</div>
                    <div className="text-xs text-gray-500 mt-0.5 truncate">
                      {activity.target}
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 whitespace-nowrap">
                    {activity.time}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
