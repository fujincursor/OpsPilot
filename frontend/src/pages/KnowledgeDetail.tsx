import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { DocumentList, UploadArea, SearchTest } from '../components/Knowledge'
import type { KnowledgeBase, Document, SearchResult } from '../types'
import { knowledgeService } from '../services'

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
  const [showSettings, setShowSettings] = useState(false)
  const [indexPaths, setIndexPaths] = useState('src')
  const [indexTrigger, setIndexTrigger] = useState('manual')
  const [updatePolicy, setUpdatePolicy] = useState('incremental')
  const [settingsMessage, setSettingsMessage] = useState('')

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
      setIndexPaths((kbData.index_paths || ['src']).join('\n'))
      setIndexTrigger(kbData.index_trigger || 'manual')
      setUpdatePolicy(kbData.update_policy || 'incremental')
    } catch (error) {
      console.error(error)
      setKnowledgeBase(null)
      setDocuments([])
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
    } catch (error) {
      console.error(error)
    }
  }

  const handleDeleteDocument = async (docId: string) => {
    try {
      await knowledgeService.deleteDocument(docId)
      setDocuments((prev) => prev.filter((d) => d.id !== docId))
      if (knowledgeBase) {
        setKnowledgeBase({
          ...knowledgeBase,
          document_count: Math.max(0, knowledgeBase.document_count - 1),
        })
      }
    } catch (error) {
      console.error(error)
    }
  }

  const handleSearch = async (query: string): Promise<SearchResult[]> => {
    if (!knowledgeBase) return []
    try {
      return await knowledgeService.searchKnowledge(
        knowledgeBase.project_id,
        query
      )
    } catch (error) {
      console.error(error)
      return []
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
            <button
              type="button"
              onClick={() => setShowSettings(true)}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
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
                  <span className="text-sm text-gray-600">已向量化</span>
                  <span className="text-sm font-medium text-green-600">
                    {
                      documents.filter((d) => d.embedding_status === 'completed')
                        .length
                    }{' '}
                    篇
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">向量化中</span>
                  <span className="text-sm font-medium text-blue-600">
                    {
                      documents.filter((d) => d.embedding_status === 'processing')
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
                  <span className="text-sm text-gray-600">向量化失败</span>
                  <span className="text-sm font-medium text-red-600">
                    {
                      documents.filter((d) => d.embedding_status === 'failed')
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
      {showSettings && knowledgeBase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-5">
            <h2 className="mb-3 text-lg font-semibold">知识库设置</h2>
            <label className="mb-3 block text-sm text-gray-600">索引范围，一行一个
              <textarea value={indexPaths} onChange={(event) => setIndexPaths(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" rows={4} />
            </label>
            <label className="mb-3 block text-sm text-gray-600">触发方式
              <select value={indexTrigger} onChange={(event) => setIndexTrigger(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2">
                <option value="manual">手动</option>
                <option value="commit">提交后</option>
              </select>
            </label>
            <label className="mb-3 block text-sm text-gray-600">更新策略
              <select value={updatePolicy} onChange={(event) => setUpdatePolicy(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2">
                <option value="incremental">增量</option>
                <option value="full">全量</option>
              </select>
            </label>
            <div className="mb-3">
              <div className="mb-2 text-sm font-medium text-gray-700">索引任务</div>
              {(knowledgeBase.index_jobs || []).length === 0 ? (
                <p className="text-sm text-gray-400">还没有索引任务</p>
              ) : (
                <div className="space-y-2">
                  {(knowledgeBase.index_jobs || []).map((job) => (
                    <div key={job.id} className="rounded-lg border border-gray-100 px-3 py-2 text-xs text-gray-600">
                      {job.status} · {job.message}
                    </div>
                  ))}
                </div>
              )}
            </div>
            {settingsMessage && <p className="mb-3 text-sm text-green-600">{settingsMessage}</p>}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={async () => {
                  const updated = await knowledgeService.updateKnowledgeBase(knowledgeBase.id, {
                    index_paths: indexPaths.split('\n').map((item) => item.trim()).filter(Boolean),
                    index_trigger: indexTrigger,
                    update_policy: updatePolicy,
                  })
                  setKnowledgeBase(updated)
                  setSettingsMessage('设置已保存')
                }}
                className="rounded-lg bg-primary px-3 py-2 text-sm text-white"
              >
                保存
              </button>
              <button
                type="button"
                onClick={async () => {
                  const updated = await knowledgeService.startIndex(knowledgeBase.id)
                  setKnowledgeBase(updated)
                  setSettingsMessage('已触发索引')
                }}
                className="rounded-lg bg-gray-800 px-3 py-2 text-sm text-white"
              >
                立即索引
              </button>
              <button type="button" onClick={() => setShowSettings(false)} className="rounded-lg bg-gray-100 px-3 py-2 text-sm">关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
