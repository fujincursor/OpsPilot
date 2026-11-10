import { useNavigate } from 'react-router-dom'
import type { Requirement } from '../../types'
import TypeIcon from './TypeIcon'
import PriorityBadge from './PriorityBadge'
import StatusBadge from './StatusBadge'

interface RequirementTableProps {
  requirements: Requirement[]
  isLoading?: boolean
}

export default function RequirementTable({ requirements, isLoading = false }: RequirementTableProps) {
  const navigate = useNavigate()

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    })
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-8 text-center">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  if (requirements.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <div className="text-5xl mb-4">📋</div>
        <h3 className="text-lg font-medium text-gray-800 mb-2">暂无需求</h3>
        <p className="text-gray-500">点击上方按钮创建第一个需求</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                类型
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                标题
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                优先级
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                负责人
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                创建时间
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {requirements.map((req) => (
              <tr
                key={req.id}
                onClick={() => navigate(`/requirements/${req.id}`)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3">
                  <TypeIcon type={req.type} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-gray-800 truncate max-w-[300px]">
                      {req.title}
                    </span>
                    {req.source && (
                      <span className="text-xs text-gray-400 mt-0.5">
                        来源: {req.source}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <PriorityBadge priority={req.priority} size="sm" />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={req.status} size="sm" />
                </td>
                <td className="px-4 py-3">
                  {req.assignee ? (
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-primary-light rounded-full flex items-center justify-center text-xs font-medium text-primary">
                        {req.assignee.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-sm text-gray-600">{req.assignee}</span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">未分配</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-500">
                    {formatDate(req.created_at)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/requirements/${req.id}`)
                    }}
                    className="px-3 py-1.5 text-xs font-medium text-primary bg-primary-light hover:bg-primary/20 rounded-lg transition-colors"
                  >
                    查看详情
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
