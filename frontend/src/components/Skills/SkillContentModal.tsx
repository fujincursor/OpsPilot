import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { projectService } from '../../services'
import type { ProjectSkill } from '../../types'

interface SkillContentModalProps {
  skill: ProjectSkill | null
  onClose: () => void
}

export default function SkillContentModal({ skill, onClose }: SkillContentModalProps) {
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!skill) return
    let cancelled = false
    setLoading(true)
    setError('')
    setContent('')
    projectService.getSkillContent(skill.key)
      .then((data) => {
        if (!cancelled) setContent(data.content)
      })
      .catch(() => {
        if (!cancelled) setError('这个技能没有可查看的说明文档。')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [skill])

  if (!skill) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="flex max-h-[80vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-gray-100 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">{skill.name}</h2>
            <p className="mt-1 text-xs text-gray-400">{skill.agent || skill.key}</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-600">
            关闭
          </button>
        </div>
        <div className="overflow-y-auto px-5 py-4">
          {loading && <p className="text-sm text-gray-500">正在读取技能说明...</p>}
          {error && <p className="text-sm text-gray-500">{error}</p>}
          {content && (
            <div className="markdown-body text-sm text-gray-700">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
