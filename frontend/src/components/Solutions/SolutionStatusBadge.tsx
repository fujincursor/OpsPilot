import type { SolutionStatus } from '../../types'

interface SolutionStatusBadgeProps {
  status: SolutionStatus
  size?: 'sm' | 'md' | 'lg'
}

const statusConfig: Record<SolutionStatus, { label: string; className: string; dotColor: string }> = {
  draft: {
    label: '草稿',
    className: 'bg-gray-100 text-gray-600',
    dotColor: 'bg-gray-400',
  },
  pending_review: {
    label: '待审核',
    className: 'bg-amber-100 text-amber-600',
    dotColor: 'bg-amber-500',
  },
  approved: {
    label: '已通过',
    className: 'bg-green-100 text-green-600',
    dotColor: 'bg-green-500',
  },
  rejected: {
    label: '已拒绝',
    className: 'bg-red-100 text-red-600',
    dotColor: 'bg-red-500',
  },
  implemented: {
    label: '已实现',
    className: 'bg-blue-100 text-blue-600',
    dotColor: 'bg-blue-500',
  },
}

const sizeConfig = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-0.5',
  lg: 'text-sm px-2.5 py-1',
}

export default function SolutionStatusBadge({ status, size = 'md' }: SolutionStatusBadgeProps) {
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
