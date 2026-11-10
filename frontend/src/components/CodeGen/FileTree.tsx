import { useState } from 'react'
import type { CodeFile, CodeFileAction } from '../../types'

interface FileTreeProps {
  files: CodeFile[]
  selectedFile?: string
  onSelectFile: (path: string) => void
}

interface TreeNode {
  name: string
  path: string
  type: 'file' | 'folder'
  action?: CodeFileAction
  language?: string
  children?: TreeNode[]
}

const actionConfig: Record<CodeFileAction, { icon: string; color: string; label: string }> = {
  create: { icon: '+', color: 'text-green-500', label: '新建' },
  modify: { icon: '~', color: 'text-amber-500', label: '修改' },
  delete: { icon: '-', color: 'text-red-500', label: '删除' },
  view: { icon: '·', color: 'text-slate-500', label: '现有' },
}

const languageIcons: Record<string, string> = {
  typescript: '📘',
  javascript: '📙',
  python: '🐍',
  java: '☕',
  go: '🔵',
  rust: '🦀',
  css: '🎨',
  html: '🌐',
  json: '📄',
  yaml: '📋',
  markdown: '📝',
  sql: '🗃️',
}

function buildTree(files: CodeFile[]): TreeNode[] {
  const root: TreeNode[] = []

  files.forEach((file) => {
    const parts = file.path.split('/')
    let current = root

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1
      const existingNode = current.find((n) => n.name === part)

      if (existingNode) {
        if (!isFile && existingNode.children) {
          current = existingNode.children
        }
      } else {
        const newNode: TreeNode = {
          name: part,
          path: parts.slice(0, index + 1).join('/'),
          type: isFile ? 'file' : 'folder',
          ...(isFile && { action: file.action, language: file.language }),
          ...(!isFile && { children: [] }),
        }
        current.push(newNode)
        if (!isFile && newNode.children) {
          current = newNode.children
        }
      }
    })
  })

  const sortTree = (nodes: TreeNode[]): TreeNode[] => {
    return nodes.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'folder' ? -1 : 1
      return a.name.localeCompare(b.name)
    }).map((node) => ({
      ...node,
      children: node.children ? sortTree(node.children) : undefined,
    }))
  }

  return sortTree(root)
}

function TreeNodeComponent({
  node,
  selectedFile,
  onSelectFile,
  depth = 0,
}: {
  node: TreeNode
  selectedFile?: string
  onSelectFile: (path: string) => void
  depth?: number
}) {
  const [isExpanded, setIsExpanded] = useState(true)

  if (node.type === 'folder') {
    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center gap-2 py-1.5 px-2 hover:bg-gray-50 rounded-md transition-colors text-left"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          <span className="text-gray-400 text-xs transition-transform duration-200" style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
            ▶
          </span>
          <span className="text-amber-500">📁</span>
          <span className="text-sm text-gray-700 font-medium">{node.name}</span>
        </button>
        {isExpanded && node.children && (
          <div>
            {node.children.map((child) => (
              <TreeNodeComponent
                key={child.path}
                node={child}
                selectedFile={selectedFile}
                onSelectFile={onSelectFile}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  const action = node.action ? actionConfig[node.action] : null
  const langIcon = node.language ? languageIcons[node.language] || '📄' : '📄'
  const isSelected = selectedFile === node.path

  return (
    <button
      onClick={() => onSelectFile(node.path)}
      className={`w-full flex items-center gap-2 py-1.5 px-2 rounded-md transition-colors text-left ${
        isSelected ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700'
      }`}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
    >
      {action && (
        <span className={`text-xs font-bold ${action.color}`} title={action.label}>
          {action.icon}
        </span>
      )}
      <span>{langIcon}</span>
      <span className={`text-sm truncate ${isSelected ? 'font-medium' : ''}`}>{node.name}</span>
    </button>
  )
}

export default function FileTree({ files, selectedFile, onSelectFile }: FileTreeProps) {
  const tree = buildTree(files)

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
          <span>📂</span>
          代码文件 ({files.length})
        </h3>
      </div>
      <div className="p-2 max-h-[500px] overflow-y-auto">
        {tree.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p className="text-sm">暂无文件</p>
          </div>
        ) : (
          tree.map((node) => (
            <TreeNodeComponent
              key={node.path}
              node={node}
              selectedFile={selectedFile}
              onSelectFile={onSelectFile}
            />
          ))
        )}
      </div>
      <div className="px-4 py-2 border-t border-gray-100 bg-gray-50 flex gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="text-green-500 font-bold">+</span> 新建
        </span>
        <span className="flex items-center gap-1">
          <span className="text-amber-500 font-bold">~</span> 修改
        </span>
        <span className="flex items-center gap-1">
          <span className="text-red-500 font-bold">-</span> 删除
        </span>
      </div>
    </div>
  )
}
