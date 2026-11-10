import type { RequirementType } from '../../types'

interface TypeIconProps {
  type: RequirementType
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const typeConfig: Record<RequirementType, { icon: string; label: string; className: string }> = {
  bug: {
    icon: '🐛',
    label: 'Bug',
    className: 'bg-red-50 text-red-600 border-red-200',
  },
  feature: {
    icon: '✨',
    label: 'Feature',
    className: 'bg-purple-50 text-purple-600 border-purple-200',
  },
  question: {
    icon: '❓',
    label: 'Question',
    className: 'bg-blue-50 text-blue-600 border-blue-200',
  },
}

const sizeConfig = {
  sm: 'text-xs px-1.5 py-0.5',
  md: 'text-sm px-2 py-1',
  lg: 'text-base px-3 py-1.5',
}

export default function TypeIcon({ type, showLabel = false, size = 'md' }: TypeIconProps) {
  const config = typeConfig[type]
  
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border font-medium ${config.className} ${sizeConfig[size]}`}
    >
      <span>{config.icon}</span>
      {showLabel && <span>{config.label}</span>}
    </span>
  )
}
