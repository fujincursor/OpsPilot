import type { DiffLine } from '../../types'

interface DiffViewerProps {
  diff: DiffLine[]
  fileName?: string
  className?: string
}

const lineTypeConfig = {
  add: {
    bgColor: 'bg-green-900/30',
    borderColor: 'border-l-green-500',
    textColor: 'text-green-300',
    prefix: '+',
    lineNumBg: 'bg-green-900/50',
  },
  remove: {
    bgColor: 'bg-red-900/30',
    borderColor: 'border-l-red-500',
    textColor: 'text-red-300',
    prefix: '-',
    lineNumBg: 'bg-red-900/50',
  },
  context: {
    bgColor: '',
    borderColor: 'border-l-transparent',
    textColor: 'text-slate-300',
    prefix: ' ',
    lineNumBg: '',
  },
}

export default function DiffViewer({ diff, fileName, className = '' }: DiffViewerProps) {
  if (diff.length === 0) {
    return (
      <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden ${className}`}>
        <div className="flex items-center justify-center h-64 text-gray-400">
          <div className="text-center">
            <div className="text-4xl mb-2">📊</div>
            <p className="text-sm">暂无差异对比</p>
          </div>
        </div>
      </div>
    )
  }

  const additions = diff.filter((l) => l.type === 'add').length
  const deletions = diff.filter((l) => l.type === 'remove').length

  return (
    <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-gray-800">差异对比</span>
          {fileName && (
            <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
              {fileName}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs font-medium">
          <span className="text-green-600 flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-green-500" />
            +{additions}
          </span>
          <span className="text-red-600 flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-500" />
            -{deletions}
          </span>
        </div>
      </div>

      <div className="overflow-auto max-h-[500px]">
        <div className="bg-slate-900 min-w-max">
          <table className="w-full border-collapse">
            <tbody>
              {diff.map((line, index) => {
                const config = lineTypeConfig[line.type]
                return (
                  <tr key={index} className={`${config.bgColor} hover:brightness-110`}>
                    <td
                      className={`select-none text-right pr-2 pl-4 py-0 text-slate-500 text-xs font-mono border-r border-slate-700/50 w-12 ${config.lineNumBg}`}
                    >
                      {line.line_number > 0 ? line.line_number : ''}
                    </td>
                    <td
                      className={`w-6 text-center font-mono text-sm ${config.textColor} border-l-2 ${config.borderColor}`}
                    >
                      {config.prefix}
                    </td>
                    <td
                      className={`pl-2 pr-4 py-0 font-mono text-sm ${config.textColor} whitespace-pre`}
                    >
                      {line.content || ' '}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
        共 {diff.length} 行变更
      </div>
    </div>
  )
}
