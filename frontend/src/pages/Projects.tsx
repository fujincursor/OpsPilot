import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ProjectCard, CreateProjectModal } from '../components/Projects'
import type { Project } from '../types'
import { projectService } from '../services'

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
      const items = await projectService.getProjects()
      setProjects(items)
    } catch (error) {
      console.error(error)
      setProjects([])
    } finally {
      setIsLoading(false)
    }
  }

  const rememberProject = (project: Project) => {
    setProjects((prev) => {
      const exists = prev.some((item) => item.id === project.id)
      if (!exists) return [project, ...prev]
      return prev.map((item) => (item.id === project.id ? project : item))
    })
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
        onCreated={rememberProject}
      />
    </div>
  )
}
