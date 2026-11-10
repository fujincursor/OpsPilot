import type { ReviewStatus } from '../../types'

interface ReviewStatusBadgeProps {
  status: ReviewStatus
  size?: 'sm' | 'md'
}

const statusConfig: Record<ReviewStatus, { label: string; className: string }> = {
  pending: {
    label: '待审核',
    className: 'bg-amber-100 text-amber-700 border-amber-200',
  },
  in_review: {
    label: '审核中',
    className: 'bg-blue-100 text-blue-700 border-blue-200',
  },
  approved: {
    label: '已通过',
    className: 'bg-green-100 text-green-700 border-green-200',
  },
  rejected: {
    label: '已拒绝',
    className: 'bg-red-100 text-red-700 border-red-200',
  },
  revision_requested: {
    label: '需修改',
    className: 'bg-orange-100 text-orange-700 border-orange-200',
  },
}

export default function ReviewStatusBadge({ status, size = 'md' }: ReviewStatusBadgeProps) {
  const config = statusConfig[status]
  const sizeClass = size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-1 text-xs'

  return (
    <span
      className={`inline-flex items-center font-medium rounded-md border ${config.className} ${sizeClass}`}
    >
      {config.label}
    </span>
  )
}
