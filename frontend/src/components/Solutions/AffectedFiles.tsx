interface AffectedFilesProps {
  files: string[]
}

const getFileIcon = (filePath: string): string => {
  const ext = filePath.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'ts':
    case 'tsx':
      return '📘'
    case 'js':
    case 'jsx':
      return '📒'
    case 'py':
      return '🐍'
    case 'sql':
      return '🗃️'
    case 'json':
      return '📋'
    case 'md':
      return '📝'
    case 'css':
    case 'scss':
      return '🎨'
    case 'html':
      return '🌐'
    default:
      return '📄'
  }
}

export default function AffectedFiles({ files }: AffectedFilesProps) {
  const items = files || []
  if (items.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg text-center text-gray-500 text-sm">
        暂无受影响的文件
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <span>📁</span>
          <span className="font-medium text-gray-800">受影响文件</span>
          <span className="px-2 py-0.5 bg-gray-200 rounded-full text-xs text-gray-600">
            {items.length} 个文件
          </span>
        </div>
      </div>
      <div className="divide-y divide-gray-100">
        {items.map((file, index) => (
          <div
            key={index}
            className="px-4 py-2.5 hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <span>{getFileIcon(file)}</span>
            <code className="text-sm text-gray-700 font-mono">{file}</code>
          </div>
        ))}
      </div>
    </div>
  )
}
