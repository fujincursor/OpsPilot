import type { Project } from '../../types'

interface ProjectCardProps {
  project: Project
  onClick: (project: Project) => void
}

const statusConfig = {
  active: {
    label: '运行中',
    className: 'bg-green-100 text-green-600',
    dot: 'bg-green-500',
  },
  inactive: {
    label: '已暂停',
    className: 'bg-amber-100 text-amber-600',
    dot: 'bg-amber-500',
  },
  archived: {
    label: '已归档',
    className: 'bg-gray-100 text-gray-600',
    dot: 'bg-gray-500',
  },
}

export default function ProjectCard({ project, onClick }: ProjectCardProps) {
  const status = statusConfig[project.status]
  const createdDate = new Date(project.created_at).toLocaleDateString('zh-CN')

  return (
    <div
      onClick={() => onClick(project)}
      className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:border-primary hover:shadow-md transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-light rounded-lg flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
            📁
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 group-hover:text-primary transition-colors">
              {project.name}
            </h3>
            <span
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ${status.className}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`}></span>
              {status.label}
            </span>
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-500 mb-4 line-clamp-2 min-h-[40px]">
        {project.description || '暂无描述'}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center gap-1 truncate max-w-[60%]">
          <span>🔗</span>
          <span className="truncate">{project.code_status === 'ready' ? '代码已导入' : '未导入源代码'}</span>
        </div>
        <span>创建于 {createdDate}</span>
      </div>
    </div>
  )
}
