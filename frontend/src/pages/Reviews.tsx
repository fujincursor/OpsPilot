import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import type {
  ReviewItem,
  ReviewItemType,
  ReviewStatus,
  RequirementPriority,
  ReviewFilters,
} from '../types'
import { projectService, reviewService } from '../services'
import type { Project } from '../types'
import { ReviewCard } from '../components/Reviews'
import { PriorityBadge } from '../components/Requirements'

const itemTypes: { value: ReviewItemType; label: string; icon: string }[] = [
  { value: 'solution', label: '方案', icon: '📋' },
  { value: 'code', label: '代码', icon: '💻' },
  { value: 'test', label: '测试', icon: '🧪' },
]

const statuses: ReviewStatus[] = ['pending', 'in_review', 'approved', 'rejected', 'revision_requested']
const priorities: RequirementPriority[] = ['low', 'medium', 'high', 'critical']

export default function Reviews() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [filteredReviews, setFilteredReviews] = useState<ReviewItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filters, setFilters] = useState<ReviewFilters>({
    item_type: (searchParams.get('type') as ReviewItemType) || undefined,
    status: (searchParams.get('status') as ReviewStatus) || undefined,
    priority: (searchParams.get('priority') as RequirementPriority) || undefined,
  })
  const [sortBy, setSortBy] = useState<'priority' | 'created_at'>('priority')
  const [projects, setProjects] = useState<Project[]>([])

  useEffect(() => {
    loadReviews()
    projectService.getProjects().then(setProjects).catch(() => setProjects([]))
  }, [])

  useEffect(() => {
    let result = [...reviews]

    if (filters.item_type) {
      result = result.filter((r) => r.item_type === filters.item_type)
    }
    if (filters.status) {
      result = result.filter((r) => r.status === filters.status)
    }
    if (filters.priority) {
      result = result.filter((r) => r.priority === filters.priority)
    }
    if (filters.project_id) {
      result = result.filter((r) => r.project_id === filters.project_id)
    }

    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
    if (sortBy === 'priority') {
      result.sort((a, b) => (priorityOrder[a.priority] ?? 9) - (priorityOrder[b.priority] ?? 9))
    } else {
      result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    }

    setFilteredReviews(result)
  }, [reviews, filters, sortBy])

  const loadReviews = async () => {
    setIsLoading(true)
    try {
      const data = await reviewService.getPendingReviews()
      setReviews(data)
    } catch (error) {
      console.error(error)
      setReviews([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFilterChange = (key: keyof ReviewFilters, value: string | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }))
    if (value) {
      searchParams.set(key === 'item_type' ? 'type' : key, value)
    } else {
      searchParams.delete(key === 'item_type' ? 'type' : key)
    }
    setSearchParams(searchParams)
  }

  const clearFilters = () => {
    setFilters({})
    setSearchParams({})
  }

  const hasActiveFilters = Object.values(filters).some((v) => v !== undefined)
  const pendingCount = reviews.filter((r) => r.status === 'pending').length
  const overdueCount = reviews.filter((r) => r.due_at && new Date(r.due_at) < new Date()).length

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-800 flex items-center gap-3">
              ✅ Review 工作台
            </h1>
            <p className="text-gray-500 mt-1">
              共 {reviews.length} 个审核项
              {pendingCount > 0 && (
                <span className="ml-2 text-amber-600 font-medium">
                  ({pendingCount} 个待审核)
                </span>
              )}
              {overdueCount > 0 && (
                <span className="ml-2 text-red-600 font-medium">
                  ⚠️ {overdueCount} 个已超时
                </span>
              )}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'priority' | 'created_at')}
              className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="priority">按优先级排序</option>
              <option value="created_at">按时间排序</option>
            </select>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">项目:</span>
              <select
                value={filters.project_id || ''}
                onChange={(event) => handleFilterChange('project_id', event.target.value || undefined)}
                className="px-2 py-1 text-xs border border-gray-200 rounded-lg bg-white"
              >
                <option value="">全部项目</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">类型:</span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleFilterChange('item_type', undefined)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-colors ${
                    !filters.item_type
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  全部
                </button>
                {itemTypes.map((t) => (
                  <button
                    key={t.value}
                    onClick={() => handleFilterChange('item_type', t.value)}
                    className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-colors flex items-center gap-1 ${
                      filters.item_type === t.value
                        ? 'bg-primary text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <span>{t.icon}</span>
                    <span>{t.label}</span>
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
                    {s === 'pending' && '待审核'}
                    {s === 'in_review' && '审核中'}
                    {s === 'approved' && '已通过'}
                    {s === 'rejected' && '已拒绝'}
                    {s === 'revision_requested' && '需修改'}
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

        {isLoading ? (
          <div className="text-center py-16">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent" />
            <p className="mt-4 text-gray-500">加载中...</p>
          </div>
        ) : filteredReviews.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <span className="text-4xl">📭</span>
            <p className="mt-4 text-gray-500">
              {hasActiveFilters ? '没有符合条件的审核项' : '暂无审核项'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredReviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>
        )}

        {hasActiveFilters && filteredReviews.length > 0 && (
          <p className="mt-4 text-center text-sm text-gray-400">
            筛选后显示 {filteredReviews.length} / {reviews.length} 个审核项
          </p>
        )}
      </div>
    </div>
  )
}
