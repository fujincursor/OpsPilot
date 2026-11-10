import { Link } from 'react-router-dom'
import type { Solution } from '../../types'
import SolutionStatusBadge from './SolutionStatusBadge'

interface SolutionCardProps {
  solution: Solution
}

const typeConfig = {
  bug_fix: {
    icon: '🐛',
    label: 'Bug 修复',
    className: 'bg-red-50 border-red-200',
    headerBg: 'bg-red-100/50',
  },
  feature_design: {
    icon: '✨',
    label: '功能设计',
    className: 'bg-purple-50 border-purple-200',
    headerBg: 'bg-purple-100/50',
  },
}

const fallbackType = {
  icon: '📄',
  label: '方案',
  className: 'bg-gray-50 border-gray-200',
  headerBg: 'bg-gray-100',
}

export default function SolutionCard({ solution }: SolutionCardProps) {
  const config = typeConfig[solution.type] || fallbackType
  const affectedFiles = solution.affected_files || []

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <Link
      to={`/solutions/${solution.id}`}
      className={`block rounded-xl border overflow-hidden transition-all hover:shadow-md ${config.className}`}
    >
      <div className={`px-4 py-3 border-b border-current/10 ${config.headerBg}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{config.icon}</span>
            <span className="font-medium text-gray-800">{config.label}</span>
          </div>
          <SolutionStatusBadge status={solution.status} size="sm" />
        </div>
      </div>
      <div className="p-4">
        <h4 className="font-semibold text-gray-800 mb-2 line-clamp-1">{solution.title}</h4>
        <p className="text-sm text-gray-600 line-clamp-2 mb-3">{solution.content}</p>
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <span>🤖</span>
            <span>{solution.created_by_agent}</span>
          </div>
          <span>{formatDate(solution.created_at)}</span>
        </div>
        {affectedFiles.length > 0 && (
          <div className="mt-3 pt-3 border-t border-current/10">
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <span>📁</span>
              <span>{affectedFiles.length} 个受影响文件</span>
            </div>
          </div>
        )}
      </div>
    </Link>
  )
}
