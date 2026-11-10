import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { DocumentList, UploadArea, SearchTest } from '../components/Knowledge'
import type { KnowledgeBase, Document, SearchResult } from '../types'
import { knowledgeService } from '../services'

const mockKnowledgeBase: KnowledgeBase = {
  id: '1',
  project_id: '1',
  name: '运维手册',
  description: '系统运维操作手册，包含常见故障处理流程和最佳实践',
  type: 'doc',
  status: 'ready',
  document_count: 45,
  created_at: '2024-01-20T08:00:00Z',
}

const mockDocuments: Document[] = [
  {
    id: '1',
    knowledge_base_id: '1',
    title: '系统部署指南',
    content: '本文档详细介绍了系统的部署流程...',
    file_path: '/docs/deployment-guide.md',
    file_type: 'md',
    embedding_status: 'ready',
    created_at: '2024-01-20T08:30:00Z',
  },
  {
    id: '2',
    knowledge_base_id: '1',
    title: '故障排查手册',
    content: '常见故障及解决方案...',
    file_path: '/docs/troubleshooting.pdf',
    file_type: 'pdf',
    embedding_status: 'ready',
    created_at: '2024-01-21T10:00:00Z',
  },
  {
    id: '3',
    knowledge_base_id: '1',
    title: '数据库维护手册',
    content: '数据库日常维护和优化...',
    file_path: '/docs/database-maintenance.docx',
    file_type: 'docx',
    embedding_status: 'indexing',
    created_at: '2024-02-01T14:00:00Z',
  },
  {
    id: '4',
    knowledge_base_id: '1',
    title: 'API 接口文档',
    content: 'RESTful API 接口规范...',
    file_path: '/docs/api-reference.json',
    file_type: 'json',
    embedding_status: 'pending',
    created_at: '2024-02-15T09:00:00Z',
  },
]

const mockSearchResults: SearchResult[] = [
  {
    document_id: '1',
    title: '系统部署指南',
    content: '系统部署需要先准备好 Docker 环境，然后执行 docker-compose up -d 命令启动所有服务...',
    score: 0.92,
    knowledge_base_name: '运维手册',
  },
  {
    document_id: '2',
    title: '故障排查手册',
    content: '如果服务无法启动，请检查端口占用情况，使用 netstat -tlnp 命令查看...',
    score: 0.78,
    knowledge_base_name: '运维手册',
  },
]

const typeConfig = {
  doc: { icon: '📄', label: '文档' },
  code: { icon: '💻', label: '代码' },
  faq: { icon: '❓', label: 'FAQ' },
}

const statusConfig = {
  pending: {
    label: '待处理',
    className: 'bg-gray-100 text-gray-600',
    dot: 'bg-gray-500',
  },
  indexing: {
    label: '索引中',
    className: 'bg-blue-100 text-blue-600',
    dot: 'bg-blue-500',
  },
  ready: {
    label: '就绪',
    className: 'bg-green-100 text-green-600',
    dot: 'bg-green-500',
  },
  error: {
    label: '错误',
    className: 'bg-red-100 text-red-600',
    dot: 'bg-red-500',
  },
}

export default function KnowledgeDetail() {
  const { kbId } = useParams<{ kbId: string }>()
  const navigate = useNavigate()
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(true)

  useEffect(() => {
    if (kbId) {
      loadData(kbId)
    }
  }, [kbId])

  const loadData = async (kbId: string) => {
    setIsLoading(true)
    setIsDocumentsLoading(true)
    try {
      const [kbData, docsData] = await Promise.all([
        knowledgeService.getKnowledgeBase(kbId),
        knowledgeService.getDocuments(kbId),
      ])
      setKnowledgeBase(kbData)
      setDocuments(docsData)
    } catch {
      console.log('Using mock data for development')
      setKnowledgeBase(mockKnowledgeBase)
      setDocuments(mockDocuments)
    } finally {
      setIsLoading(false)
      setIsDocumentsLoading(false)
    }
  }

  const handleUpload = async (file: File) => {
    if (!kbId) return
    try {
      const newDoc = await knowledgeService.uploadDocument(kbId, file)
      setDocuments((prev) => [newDoc, ...prev])
      if (knowledgeBase) {
        setKnowledgeBase({
          ...knowledgeBase,
          document_count: knowledgeBase.document_count + 1,
        })
      }
    } catch {
      const mockNewDoc: Document = {
        id: String(Date.now()),
        knowledge_base_id: kbId,
        title: file.name,
        content: '',
        file_path: `/uploads/${file.name}`,
        file_type: file.name.split('.').pop() || 'unknown',
        embedding_status: 'pending',
        created_at: new Date().toISOString(),
      }
      setDocuments((prev) => [mockNewDoc, ...prev])
      if (knowledgeBase) {
        setKnowledgeBase({
          ...knowledgeBase,
          document_count: knowledgeBase.document_count + 1,
        })
      }
    }
  }

  const handleDeleteDocument = async (docId: string) => {
    try {
      await knowledgeService.deleteDocument(docId)
    } catch {
      console.log('Mock delete for development')
    }
    setDocuments((prev) => prev.filter((d) => d.id !== docId))
    if (knowledgeBase) {
      setKnowledgeBase({
        ...knowledgeBase,
        document_count: Math.max(0, knowledgeBase.document_count - 1),
      })
    }
  }

  const handleSearch = async (query: string): Promise<SearchResult[]> => {
    if (!knowledgeBase) return []
    try {
      return await knowledgeService.searchKnowledge(
        knowledgeBase.project_id,
        query
      )
    } catch {
      console.log('Using mock search results for development')
      return mockSearchResults.filter(
        (r) =>
          r.content.toLowerCase().includes(query.toLowerCase()) ||
          r.title.toLowerCase().includes(query.toLowerCase())
      )
    }
  }

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

  if (!knowledgeBase) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">
            知识库不存在
          </h3>
          <p className="text-gray-500 mb-6">找不到该知识库，请检查链接是否正确</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors"
          >
            返回上一页
          </button>
        </div>
      </div>
    )
  }

  const type = typeConfig[knowledgeBase.type]
  const status = statusConfig[knowledgeBase.status]
  const createdDate = new Date(knowledgeBase.created_at).toLocaleDateString(
    'zh-CN'
  )

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() =>
            navigate(`/projects/${knowledgeBase.project_id}/knowledge`)
          }
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-6 transition-colors"
        >
          <span>←</span>
          返回知识库列表
        </button>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-primary-light rounded-xl flex items-center justify-center text-3xl">
                {type.icon}
              </div>
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-2xl font-semibold text-gray-800">
                    {knowledgeBase.name}
                  </h1>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${status.dot}`}
                    ></span>
                    {status.label}
                  </span>
                </div>
                <p className="text-gray-500 mb-3 max-w-2xl">
                  {knowledgeBase.description || '暂无描述'}
                </p>
                <div className="flex items-center gap-6 text-sm text-gray-400">
                  <span className="flex items-center gap-1.5">
                    <span>{type.icon}</span>
                    {type.label}类型
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span>📑</span>
                    {knowledgeBase.document_count} 篇文档
                  </span>
                  <span>创建于 {createdDate}</span>
                </div>
              </div>
            </div>
            <button className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              ⚙️ 设置
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span>📤</span>
                上传文档
              </h2>
              <UploadArea onUpload={handleUpload} />
            </div>

            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span>📑</span>
                文档列表
                <span className="text-sm font-normal text-gray-500">
                  ({documents.length} 篇)
                </span>
              </h2>
              <DocumentList
                documents={documents}
                isLoading={isDocumentsLoading}
                onDelete={handleDeleteDocument}
              />
            </div>
          </div>

          <div className="space-y-6">
            <SearchTest onSearch={handleSearch} />

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span>📊</span>
                索引统计
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">已索引文档</span>
                  <span className="text-sm font-medium text-green-600">
                    {
                      documents.filter((d) => d.embedding_status === 'ready')
                        .length
                    }{' '}
                    篇
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">索引中</span>
                  <span className="text-sm font-medium text-blue-600">
                    {
                      documents.filter((d) => d.embedding_status === 'indexing')
                        .length
                    }{' '}
                    篇
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">待处理</span>
                  <span className="text-sm font-medium text-gray-600">
                    {
                      documents.filter((d) => d.embedding_status === 'pending')
                        .length
                    }{' '}
                    篇
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">索引失败</span>
                  <span className="text-sm font-medium text-red-600">
                    {
                      documents.filter((d) => d.embedding_status === 'error')
                        .length
                    }{' '}
                    篇
                  </span>
                </div>
                <div className="pt-3 mt-3 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-800">
                      总计
                    </span>
                    <span className="text-sm font-semibold text-gray-800">
                      {documents.length} 篇文档
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
