import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type {
  Requirement,
  RequirementType,
  RequirementStatus,
  RequirementPriority,
  RequirementFilters,
  CreateRequirementRequest,
  Project,
} from '../types'
import { requirementService, projectService } from '../services'
import {
  RequirementTable,
  CreateRequirementModal,
  TypeIcon,
  PriorityBadge,
} from '../components/Requirements'

export default function Requirements() {
  const { id: projectId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [requirements, setRequirements] = useState<Requirement[]>([])
  const [filteredRequirements, setFilteredRequirements] = useState<Requirement[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [filters, setFilters] = useState<RequirementFilters>({})

  useEffect(() => {
    if (projectId) {
      loadData(projectId)
    }
  }, [projectId])

  useEffect(() => {
    let result = [...requirements]
    if (filters.type) {
      result = result.filter((r) => r.type === filters.type)
    }
    if (filters.status) {
      result = result.filter((r) => r.status === filters.status)
    }
    if (filters.priority) {
      result = result.filter((r) => r.priority === filters.priority)
    }
    setFilteredRequirements(result)
  }, [requirements, filters])

  const loadData = async (projectId: string) => {
    setIsLoading(true)
    try {
      const [projectData, reqs] = await Promise.all([
        projectService.getProject(projectId),
        requirementService.getRequirements(projectId, filters),
      ])
      setProject(projectData)
      setRequirements(reqs)
    } catch (error) {
      console.error(error)
      setProject(null)
      setRequirements([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateRequirement = async (data: CreateRequirementRequest) => {
    if (!projectId) return
    try {
      const newReq = await requirementService.createRequirement(projectId, data)
      setRequirements((prev) => [newReq, ...prev])
    } catch (error) {
      console.error(error)
    }
  }

  const handleFilterChange = (key: keyof RequirementFilters, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }))
  }

  const clearFilters = () => {
    setFilters({})
  }

  const types: RequirementType[] = ['bug', 'feature', 'question']
  const statuses: RequirementStatus[] = ['pending', 'analyzing', 'designing', 'reviewing', 'coding', 'testing', 'completed', 'closed']
  const priorities: RequirementPriority[] = ['low', 'medium', 'high', 'critical']

  const hasActiveFilters = Object.values(filters).some((v) => v !== undefined)

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate(`/projects/${projectId}`)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回项目详情
        </button>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-800 flex items-center gap-3">
              📋 需求管理
              {project && (
                <span className="text-base font-normal text-gray-500">
                  - {project.name}
                </span>
              )}
            </h1>
            <p className="text-gray-500 mt-1">
              共 {requirements.length} 个需求
              {hasActiveFilters && ` (筛选后 ${filteredRequirements.length} 个)`}
            </p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
          >
            ➕ 创建需求
          </button>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">类型:</span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleFilterChange('type', undefined)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-colors ${
                    !filters.type
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  全部
                </button>
                {types.map((t) => (
                  <button
                    key={t}
                    onClick={() => handleFilterChange('type', t)}
                    className={`transition-all ${
                      filters.type === t
                        ? 'ring-2 ring-primary ring-offset-1'
                        : 'opacity-70 hover:opacity-100'
                    }`}
                  >
                    <TypeIcon type={t} size="sm" />
                  </button>
                ))}
              </div>
            </div>

            <div className="w-px h-6 bg-gray-200" />

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">状态:</span>
              <select
                value={filters.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
                className="px-2.5 py-1 text-xs font-medium rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">全部</option>
                {statuses.map((s) => (
                  <option key={s} value={s}>
                    {s === 'pending' && '待处理'}
                    {s === 'analyzing' && '分析中'}
                    {s === 'designing' && '设计中'}
                    {s === 'reviewing' && '审核中'}
                    {s === 'coding' && '编码中'}
                    {s === 'testing' && '测试中'}
                    {s === 'completed' && '已完成'}
                    {s === 'closed' && '已关闭'}
                  </option>
                ))}
              </select>
            </div>

            <div className="w-px h-6 bg-gray-200" />

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">优先级:</span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleFilterChange('priority', undefined)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-colors ${
                    !filters.priority
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  全部
                </button>
                {priorities.map((p) => (
                  <button
                    key={p}
                    onClick={() => handleFilterChange('priority', p)}
                    className={`transition-all ${
                      filters.priority === p
                        ? 'ring-2 ring-primary ring-offset-1'
                        : 'opacity-70 hover:opacity-100'
                    }`}
                  >
                    <PriorityBadge priority={p} size="sm" />
                  </button>
                ))}
              </div>
            </div>

            {hasActiveFilters && (
              <>
                <div className="w-px h-6 bg-gray-200" />
                <button
                  onClick={clearFilters}
                  className="px-2.5 py-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                >
                  清除筛选
                </button>
              </>
            )}
          </div>
        </div>

        <RequirementTable requirements={filteredRequirements} isLoading={isLoading} />

        {projectId && (
          <CreateRequirementModal
            isOpen={isCreateModalOpen}
            projectId={projectId}
            onClose={() => setIsCreateModalOpen(false)}
            onSubmit={handleCreateRequirement}
          />
        )}
      </div>
    </div>
  )
}
