import type { KnowledgeBase } from '../../types'

interface KnowledgeCardProps {
  knowledgeBase: KnowledgeBase
  onClick: (kb: KnowledgeBase) => void
}

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

export default function KnowledgeCard({
  knowledgeBase,
  onClick,
}: KnowledgeCardProps) {
  const type = typeConfig[knowledgeBase.type]
  const status = statusConfig[knowledgeBase.status]
  const createdDate = new Date(knowledgeBase.created_at).toLocaleDateString(
    'zh-CN'
  )

  return (
    <div
      onClick={() => onClick(knowledgeBase)}
      className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:border-primary hover:shadow-md transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-primary-light rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            {type.icon}
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 group-hover:text-primary transition-colors">
              {knowledgeBase.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-500">{type.label}</span>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${status.className}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`}></span>
                {status.label}
              </span>
            </div>
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-500 mb-4 line-clamp-2 min-h-[40px]">
        {knowledgeBase.description || '暂无描述'}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center gap-1">
          <span>📑</span>
          <span>{knowledgeBase.document_count} 篇文档</span>
        </div>
        <span>创建于 {createdDate}</span>
      </div>
    </div>
  )
}
