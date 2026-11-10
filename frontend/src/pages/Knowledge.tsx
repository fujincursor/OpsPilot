import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { KnowledgeCard, CreateKnowledgeModal } from '../components/Knowledge'
import type { KnowledgeBase, CreateKnowledgeBaseRequest, Project } from '../types'
import { knowledgeService, projectService } from '../services'

const mockKnowledgeBases: KnowledgeBase[] = [
  {
    id: '1',
    project_id: '1',
    name: '运维手册',
    description: '系统运维操作手册，包含常见故障处理流程和最佳实践',
    type: 'doc',
    status: 'ready',
    document_count: 45,
    created_at: '2024-01-20T08:00:00Z',
  },
  {
    id: '2',
    project_id: '1',
    name: '代码仓库索引',
    description: '项目代码库的向量索引，支持代码语义搜索',
    type: 'code',
    status: 'indexing',
    document_count: 1234,
    created_at: '2024-02-01T10:00:00Z',
  },
  {
    id: '3',
    project_id: '1',
    name: '常见问题',
    description: '用户和运维人员常见问题解答',
    type: 'faq',
    status: 'ready',
    document_count: 89,
    created_at: '2024-02-15T14:00:00Z',
  },
  {
    id: '4',
    project_id: '1',
    name: 'API 文档',
    description: '接口文档和使用示例',
    type: 'doc',
    status: 'pending',
    document_count: 0,
    created_at: '2024-03-01T09:00:00Z',
  },
]

const statusSummaryConfig = {
  pending: { label: '待处理', color: 'gray' },
  indexing: { label: '索引中', color: 'blue' },
  ready: { label: '已就绪', color: 'green' },
  error: { label: '有错误', color: 'red' },
}

export default function Knowledge() {
  const { id: projectId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [filterType, setFilterType] = useState<string>('all')

  useEffect(() => {
    if (projectId) {
      loadData(projectId)
    }
  }, [projectId])

  const loadData = async (projectId: string) => {
    setIsLoading(true)
    try {
      const [projectData, kbData] = await Promise.all([
        projectService.getProject(projectId),
        knowledgeService.getKnowledgeBases(projectId),
      ])
      setProject(projectData)
      setKnowledgeBases(kbData)
    } catch {
      console.log('Using mock data for development')
      setProject({
        id: projectId,
        name: '用户服务系统',
        description: '核心用户认证与授权服务',
        repo_url: 'https://github.com/company/user-service',
        status: 'active',
        created_at: '2024-01-15T08:00:00Z',
        updated_at: '2024-03-10T14:30:00Z',
      })
      setKnowledgeBases(mockKnowledgeBases)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateKnowledgeBase = async (data: CreateKnowledgeBaseRequest) => {
    if (!projectId) return
    try {
      const newKb = await knowledgeService.createKnowledgeBase(projectId, data)
      setKnowledgeBases((prev) => [newKb, ...prev])
    } catch {
      const mockNewKb: KnowledgeBase = {
        id: String(Date.now()),
        project_id: projectId,
        name: data.name,
        description: data.description,
        type: data.type,
        status: 'pending',
        document_count: 0,
        created_at: new Date().toISOString(),
      }
      setKnowledgeBases((prev) => [mockNewKb, ...prev])
    }
  }

  const handleKnowledgeCardClick = (kb: KnowledgeBase) => {
    navigate(`/knowledge/${kb.id}`)
  }

  const filteredKnowledgeBases = knowledgeBases.filter(
    (kb) => filterType === 'all' || kb.type === filterType
  )

  const statusCounts = knowledgeBases.reduce(
    (acc, kb) => {
      acc[kb.status]++
      return acc
    },
    { pending: 0, indexing: 0, ready: 0, error: 0 }
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

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

        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-800 mb-2">
              📚 知识库管理
            </h1>
            <p className="text-gray-500">
              {project?.name} - 管理项目相关的文档、代码和FAQ知识库
            </p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            ➕ 创建知识库
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          {(Object.entries(statusSummaryConfig) as [keyof typeof statusSummaryConfig, typeof statusSummaryConfig[keyof typeof statusSummaryConfig]][]).map(
            ([status, config]) => (
              <div
                key={status}
                className="bg-white rounded-xl border border-gray-200 p-4"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full bg-${config.color}-500`}
                  />
                  <div>
                    <div className="text-2xl font-semibold text-gray-800">
                      {statusCounts[status]}
                    </div>
                    <div className="text-sm text-gray-500">{config.label}</div>
                  </div>
                </div>
              </div>
            )
          )}
        </div>

        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm text-gray-500">筛选：</span>
          {[
            { value: 'all', label: '全部' },
            { value: 'doc', label: '📄 文档' },
            { value: 'code', label: '💻 代码' },
            { value: 'faq', label: '❓ FAQ' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setFilterType(option.value)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                filterType === option.value
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        {filteredKnowledgeBases.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">
              暂无知识库
            </h3>
            <p className="text-gray-500 mb-6">
              创建知识库来管理项目相关的文档和知识
            </p>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors"
            >
              创建第一个知识库
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredKnowledgeBases.map((kb) => (
              <KnowledgeCard
                key={kb.id}
                knowledgeBase={kb}
                onClick={handleKnowledgeCardClick}
              />
            ))}
          </div>
        )}
      </div>

      <CreateKnowledgeModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateKnowledgeBase}
      />
    </div>
  )
}
