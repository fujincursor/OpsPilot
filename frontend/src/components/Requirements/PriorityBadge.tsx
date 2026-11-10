import type { RequirementPriority } from '../../types'

interface PriorityBadgeProps {
  priority: RequirementPriority
  size?: 'sm' | 'md' | 'lg'
}

const priorityConfig: Record<RequirementPriority, { label: string; className: string }> = {
  low: {
    label: 'Low',
    className: 'bg-gray-100 text-gray-600 border-gray-200',
  },
  medium: {
    label: 'Medium',
    className: 'bg-blue-100 text-blue-600 border-blue-200',
  },
  high: {
    label: 'High',
    className: 'bg-orange-100 text-orange-600 border-orange-200',
  },
  critical: {
    label: 'Critical',
    className: 'bg-red-100 text-red-600 border-red-200',
  },
}

const sizeConfig = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-0.5',
  lg: 'text-sm px-2.5 py-1',
}

export default function PriorityBadge({ priority, size = 'md' }: PriorityBadgeProps) {
  const config = priorityConfig[priority]
  
  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${config.className} ${sizeConfig[size]}`}
    >
      {config.label}
    </span>
  )
}
