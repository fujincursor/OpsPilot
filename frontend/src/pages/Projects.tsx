import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ProjectCard, CreateProjectModal } from '../components/Projects'
import type { Project, CreateProjectRequest } from '../types'
import { projectService } from '../services'

const mockProjects: Project[] = [
  {
    id: '1',
    name: '用户服务系统',
    description: '核心用户认证与授权服务，支持 OAuth2.0 和 SSO 登录',
    repo_url: 'https://github.com/company/user-service',
    status: 'active',
    created_at: '2024-01-15T08:00:00Z',
    updated_at: '2024-03-10T14:30:00Z',
  },
  {
    id: '2',
    name: '订单处理平台',
    description: '电商订单全生命周期管理，包含库存同步和物流追踪',
    repo_url: 'https://github.com/company/order-platform',
    status: 'active',
    created_at: '2024-02-20T10:00:00Z',
    updated_at: '2024-03-08T09:15:00Z',
  },
  {
    id: '3',
    name: '数据分析引擎',
    description: '实时数据处理和可视化报表生成',
    repo_url: 'https://github.com/company/data-analytics',
    status: 'inactive',
    created_at: '2023-11-05T12:00:00Z',
    updated_at: '2024-02-28T16:45:00Z',
  },
  {
    id: '4',
    name: '消息推送服务',
    description: '多渠道消息推送（短信、邮件、App Push）',
    repo_url: 'https://github.com/company/notification-service',
    status: 'active',
    created_at: '2024-03-01T09:00:00Z',
    updated_at: '2024-03-10T11:20:00Z',
  },
  {
    id: '5',
    name: '旧版 CRM 系统',
    description: '客户关系管理系统（已迁移至新平台）',
    repo_url: 'https://github.com/company/legacy-crm',
    status: 'archived',
    created_at: '2022-06-10T08:00:00Z',
    updated_at: '2023-12-15T18:00:00Z',
  },
]

export default function Projects() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [filter, setFilter] = useState<'all' | Project['status']>('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setIsLoading(true)
    try {
      const response = await projectService.getProjects()
      setProjects(response.data)
    } catch {
      console.log('Using mock data for development')
      setProjects(mockProjects)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateProject = async (data: CreateProjectRequest) => {
    try {
      const newProject = await projectService.createProject(data)
      setProjects((prev) => [newProject, ...prev])
    } catch {
      const newProject: Project = {
        id: Date.now().toString(),
        ...data,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setProjects((prev) => [newProject, ...prev])
    }
  }

  const handleProjectClick = (project: Project) => {
    navigate(`/projects/${project.id}`)
  }

  const filteredProjects = projects.filter((project) => {
    const matchesFilter = filter === 'all' || project.status === filter
    const matchesSearch =
      searchQuery === '' ||
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.description.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const statusCounts = {
    all: projects.length,
    active: projects.filter((p) => p.status === 'active').length,
    inactive: projects.filter((p) => p.status === 'inactive').length,
    archived: projects.filter((p) => p.status === 'archived').length,
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-800">项目管理</h1>
            <p className="text-gray-500 mt-1">管理和配置您的运维项目</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors shadow-sm"
          >
            <span>➕</span>
            创建项目
          </button>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="p-4 flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                  🔍
                </span>
                <input
                  type="text"
                  placeholder="搜索项目名称或描述..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </div>
            <div className="flex gap-2">
              {(
                [
                  { key: 'all', label: '全部' },
                  { key: 'active', label: '运行中' },
                  { key: 'inactive', label: '已暂停' },
                  { key: 'archived', label: '已归档' },
                ] as const
              ).map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    filter === key
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {label}
                  <span className="ml-1.5 text-xs opacity-80">
                    ({statusCounts[key]})
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-500">加载中...</p>
            </div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📁</div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">
              {searchQuery ? '未找到匹配的项目' : '暂无项目'}
            </h3>
            <p className="text-gray-500 mb-6">
              {searchQuery ? '尝试调整搜索条件' : '点击上方按钮创建您的第一个项目'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => setIsModalOpen(true)}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors"
              >
                创建项目
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={handleProjectClick}
              />
            ))}
          </div>
        )}
      </div>

      <CreateProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateProject}
      />
    </div>
  )
}
