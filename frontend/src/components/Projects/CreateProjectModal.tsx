import { useState } from 'react'
import type { Project } from '../../types'
import { projectErrorMessage, projectService } from '../../services/projectService'

interface CreateProjectModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (project: Project) => void
}

type SourceMode = 'git' | 'upload' | 'none'

export default function CreateProjectModal({
  isOpen,
  onClose,
  onCreated,
}: CreateProjectModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [source, setSource] = useState<SourceMode>('git')
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [createdId, setCreatedId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const reset = () => {
    setName('')
    setDescription('')
    setSource('git')
    setRepoUrl('')
    setBranch('')
    setFile(null)
    setCreatedId(null)
    setError('')
  }

  const close = () => {
    if (isSubmitting) return
    reset()
    onClose()
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!name.trim()) {
      setError('项目名称不能为空')
      return
    }
    if (source === 'git' && !/^https?:\/\/.+|^git@.+/i.test(repoUrl.trim())) {
      setError('请输入 http(s) 或 git@ 开头的仓库地址')
      return
    }
    if (source === 'upload' && !file) {
      setError('请选择 zip 压缩包')
      return
    }

    setIsSubmitting(true)
    setError('')
    try {
      let projectId = createdId
      if (!projectId) {
        const created = await projectService.createProject({
          name: name.trim(),
          description: description.trim(),
          repo_url: source === 'git' ? repoUrl.trim() : '',
        })
        projectId = created.id
        setCreatedId(created.id)
        onCreated(created)
      }
      if (source === 'git') {
        const imported = await projectService.importGit(projectId, repoUrl.trim(), branch.trim())
        onCreated(imported)
      } else if (source === 'upload' && file) {
        const imported = await projectService.uploadSource(projectId, file)
        onCreated(imported)
      }
      reset()
      onClose()
    } catch (caught) {
      setError(projectErrorMessage(caught, '项目已创建，但源代码导入失败。可以稍后在项目设置里重试。'))
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={close} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">创建新项目</h2>
          <p className="text-sm text-gray-500 mt-1">
            源代码会保存到服务器上的项目目录。后续方案和代码生成只改这份已上传的代码，不改工作目录。
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                项目名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="例如：用户服务系统"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">项目描述</label>
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="简要描述项目的功能和用途..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              />
            </div>

            <fieldset>
              <legend className="block text-sm font-medium text-gray-700 mb-1.5">源代码</legend>
              <div className="flex flex-wrap gap-2">
                {([
                  ['git', '从 GitHub 克隆'],
                  ['upload', '上传压缩包'],
                  ['none', '暂不导入'],
                ] as const).map(([value, label]) => (
                  <label key={value} className={`rounded-lg border px-3 py-2 text-sm cursor-pointer ${source === value ? 'border-primary bg-primary-light text-primary' : 'border-gray-200 text-gray-600'}`}>
                    <input
                      type="radio"
                      name="code-source"
                      className="mr-2"
                      checked={source === value}
                      onChange={() => setSource(value)}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </fieldset>

            {source === 'git' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">仓库地址</label>
                  <input
                    type="text"
                    value={repoUrl}
                    onChange={(event) => setRepoUrl(event.target.value)}
                    placeholder="https://github.com/your-org/your-repo"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">分支</label>
                  <input
                    type="text"
                    value={branch}
                    onChange={(event) => setBranch(event.target.value)}
                    placeholder="留空则使用仓库默认分支"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </>
            )}

            {source === 'upload' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">zip 压缩包</label>
                <input
                  type="file"
                  accept=".zip,application/zip"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                  className="block w-full text-sm text-gray-600"
                />
                <p className="mt-1 text-xs text-gray-400">最大 50MB。压缩包里如果只有一层目录，会自动展开。</p>
              </div>
            )}

            {source === 'none' && (
              <p className="text-sm text-gray-500">
                未导入代码时，方案不会列出具体文件。可以稍后在项目设置中克隆或上传。
              </p>
            )}

            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>

          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3 justify-end">
            <button
              type="button"
              onClick={close}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (source === 'none' ? '创建中...' : '导入中...') : createdId ? '重试导入' : '创建项目'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
