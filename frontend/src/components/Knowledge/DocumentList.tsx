import { useState } from 'react'
import type { Document } from '../../types'

interface DocumentListProps {
  documents: Document[]
  isLoading: boolean
  onDelete: (docId: string) => void
}

const statusConfig = {
  pending: {
    label: '待处理',
    className: 'bg-gray-100 text-gray-600',
  },
  indexing: {
    label: '索引中',
    className: 'bg-blue-100 text-blue-600',
  },
  ready: {
    label: '已索引',
    className: 'bg-green-100 text-green-600',
  },
  error: {
    label: '索引失败',
    className: 'bg-red-100 text-red-600',
  },
}

const fileTypeIcons: Record<string, string> = {
  pdf: '📕',
  doc: '📘',
  docx: '📘',
  md: '📝',
  txt: '📄',
  json: '📋',
  yaml: '⚙️',
  yml: '⚙️',
  py: '🐍',
  js: '🟨',
  ts: '🔷',
  jsx: '⚛️',
  tsx: '⚛️',
  go: '🔵',
  java: '☕',
  default: '📄',
}

function getFileIcon(fileType: string): string {
  return fileTypeIcons[fileType.toLowerCase()] || fileTypeIcons.default
}

export default function DocumentList({
  documents,
  isLoading,
  onDelete,
}: DocumentListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (docId: string) => {
    if (window.confirm('确定要删除这篇文档吗？此操作不可恢复。')) {
      setDeletingId(docId)
      try {
        await onDelete(docId)
      } finally {
        setDeletingId(null)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="ml-3 text-gray-500">加载文档列表...</span>
        </div>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <div className="text-5xl mb-4">📂</div>
        <h3 className="text-lg font-medium text-gray-800 mb-2">暂无文档</h3>
        <p className="text-sm text-gray-500">
          上传文档后，系统会自动进行向量索引
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              文档
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              类型
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              状态
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              创建时间
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {documents.map((doc) => {
            const status = statusConfig[doc.embedding_status]
            const createdDate = new Date(doc.created_at).toLocaleString('zh-CN')
            const fileIcon = getFileIcon(doc.file_type)

            return (
              <tr
                key={doc.id}
                className="hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{fileIcon}</span>
                    <div>
                      <div className="text-sm font-medium text-gray-800">
                        {doc.title}
                      </div>
                      <div className="text-xs text-gray-400 truncate max-w-xs">
                        {doc.file_path}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-600 uppercase">
                    {doc.file_type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.className}`}
                  >
                    {doc.embedding_status === 'indexing' && (
                      <span className="w-2 h-2 mr-1.5 rounded-full bg-blue-500 animate-pulse" />
                    )}
                    {status.label}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {createdDate}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    className="text-sm text-red-500 hover:text-red-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {deletingId === doc.id ? '删除中...' : '删除'}
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
