import type { TestStatus, TestResultStatus } from '../../types'

interface TestStatusBadgeProps {
  status: TestStatus | TestResultStatus
  size?: 'sm' | 'md' | 'lg'
}

const testStatusConfig: Record<TestStatus, { label: string; className: string; dotColor: string }> = {
  pending: {
    label: '待处理',
    className: 'bg-gray-100 text-gray-600',
    dotColor: 'bg-gray-400',
  },
  generating: {
    label: '生成用例',
    className: 'bg-blue-100 text-blue-600',
    dotColor: 'bg-blue-500 animate-pulse',
  },
  running: {
    label: '运行中',
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

const resultStatusConfig: Record<TestResultStatus, { label: string; className: string; dotColor: string }> = {
  passed: {
    label: '通过',
    className: 'bg-green-100 text-green-600',
    dotColor: 'bg-green-500',
  },
  failed: {
    label: '失败',
    className: 'bg-red-100 text-red-600',
    dotColor: 'bg-red-500',
  },
  skipped: {
    label: '跳过',
    className: 'bg-gray-100 text-gray-600',
    dotColor: 'bg-gray-400',
  },
}

const sizeConfig = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-0.5',
  lg: 'text-sm px-2.5 py-1',
}

function isTestStatus(status: TestStatus | TestResultStatus): status is TestStatus {
  return ['pending', 'generating', 'running', 'completed', 'failed'].includes(status)
}

export default function TestStatusBadge({ status, size = 'md' }: TestStatusBadgeProps) {
  const config = isTestStatus(status) ? testStatusConfig[status] : resultStatusConfig[status]

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${config.className} ${sizeConfig[size]}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor}`} />
      {config.label}
    </span>
  )
}

export { testStatusConfig, resultStatusConfig }
