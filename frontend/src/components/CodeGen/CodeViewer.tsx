import type { CodeFile, CodeFileAction } from '../../types'

interface CodeViewerProps {
  file: CodeFile | null
  className?: string
}

const actionLabels: Record<CodeFileAction, { text: string; bgColor: string }> = {
  create: { text: '新建文件', bgColor: 'bg-green-500' },
  modify: { text: '修改文件', bgColor: 'bg-amber-500' },
  delete: { text: '删除文件', bgColor: 'bg-red-500' },
}

const languageNames: Record<string, string> = {
  typescript: 'TypeScript',
  javascript: 'JavaScript',
  python: 'Python',
  java: 'Java',
  go: 'Go',
  rust: 'Rust',
  css: 'CSS',
  html: 'HTML',
  json: 'JSON',
  yaml: 'YAML',
  markdown: 'Markdown',
  sql: 'SQL',
  shell: 'Shell',
  bash: 'Bash',
}

export default function CodeViewer({ file, className = '' }: CodeViewerProps) {
  if (!file) {
    return (
      <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden ${className}`}>
        <div className="flex items-center justify-center h-64 text-gray-400">
          <div className="text-center">
            <div className="text-4xl mb-2">📄</div>
            <p className="text-sm">选择文件查看代码</p>
          </div>
        </div>
      </div>
    )
  }

  const lines = file.content.split('\n')
  const actionConfig = actionLabels[file.action]
  const languageName = languageNames[file.language] || file.language

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(file.content)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3">
          <span className="text-sm font-mono text-gray-700 truncate">{file.path}</span>
          <span className={`text-xs px-2 py-0.5 rounded text-white ${actionConfig.bgColor}`}>
            {actionConfig.text}
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600">
            {languageName}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
          title="复制代码"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
      </div>

      <div className="overflow-auto max-h-[600px]">
        <div className="bg-slate-900 min-w-max">
          <table className="w-full border-collapse">
            <tbody>
              {lines.map((line, index) => (
                <tr key={index} className="hover:bg-slate-800/50">
                  <td className="select-none text-right pr-4 pl-4 py-0 text-slate-500 text-xs font-mono border-r border-slate-700/50 sticky left-0 bg-slate-900/95">
                    {index + 1}
                  </td>
                  <td className="pl-4 pr-4 py-0 font-mono text-sm text-slate-100 whitespace-pre">
                    {line || ' '}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 flex items-center justify-between text-xs text-gray-500">
        <span>{lines.length} 行</span>
        <span>{file.content.length} 字符</span>
      </div>
    </div>
  )
}
