import type { RequirementStatus } from '../../types'

interface StatusBadgeProps {
  status: RequirementStatus
  size?: 'sm' | 'md' | 'lg'
}

const statusConfig: Record<RequirementStatus, { label: string; className: string; dotColor: string }> = {
  pending: {
    label: '待处理',
    className: 'bg-gray-100 text-gray-600',
    dotColor: 'bg-gray-400',
  },
  analyzing: {
    label: '分析中',
    className: 'bg-blue-100 text-blue-600',
    dotColor: 'bg-blue-500',
  },
  designing: {
    label: '设计中',
    className: 'bg-purple-100 text-purple-600',
    dotColor: 'bg-purple-500',
  },
  reviewing: {
    label: '审核中',
    className: 'bg-amber-100 text-amber-600',
    dotColor: 'bg-amber-500',
  },
  coding: {
    label: '编码中',
    className: 'bg-cyan-100 text-cyan-600',
    dotColor: 'bg-cyan-500',
  },
  testing: {
    label: '测试中',
    className: 'bg-indigo-100 text-indigo-600',
    dotColor: 'bg-indigo-500',
  },
  completed: {
    label: '已完成',
    className: 'bg-green-100 text-green-600',
    dotColor: 'bg-green-500',
  },
  closed: {
    label: '已关闭',
    className: 'bg-gray-200 text-gray-500',
    dotColor: 'bg-gray-400',
  },
}

const sizeConfig = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-0.5',
  lg: 'text-sm px-2.5 py-1',
}

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status]
  
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${config.className} ${sizeConfig[size]}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor}`} />
      {config.label}
    </span>
  )
}

export { statusConfig }
