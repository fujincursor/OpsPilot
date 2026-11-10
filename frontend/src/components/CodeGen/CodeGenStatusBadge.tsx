import type { CodeGenStatus } from '../../types'

interface CodeGenStatusBadgeProps {
  status: CodeGenStatus
  size?: 'sm' | 'md' | 'lg'
}

const statusConfig: Record<CodeGenStatus, { label: string; className: string; dotColor: string }> = {
  pending: {
    label: '待处理',
    className: 'bg-gray-100 text-gray-600',
    dotColor: 'bg-gray-400',
  },
  generating: {
    label: '生成中',
    className: 'bg-blue-100 text-blue-600',
    dotColor: 'bg-blue-500 animate-pulse',
  },
  linting: {
    label: '代码检查中',
    className: 'bg-amber-100 text-amber-600',
    dotColor: 'bg-amber-500 animate-pulse',
  },
  completed: {
    label: '已完成',
    className: 'bg-green-100 text-green-600',
    dotColor: 'bg-green-500',
  },
  failed: {
    label: '失败',
    className: 'bg-red-100 text-red-600',
    dotColor: 'bg-red-500',
  },
}

const sizeConfig = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-0.5',
  lg: 'text-sm px-2.5 py-1',
}

export default function CodeGenStatusBadge({ status, size = 'md' }: CodeGenStatusBadgeProps) {
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
