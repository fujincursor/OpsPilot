import { useState } from 'react'
import type { CreateProjectRequest } from '../../types'

interface CreateProjectModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CreateProjectRequest) => Promise<void>
}

export default function CreateProjectModal({
  isOpen,
  onClose,
  onSubmit,
}: CreateProjectModalProps) {
  const [formData, setFormData] = useState<CreateProjectRequest>({
    name: '',
    description: '',
    repo_url: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<Partial<CreateProjectRequest>>({})

  const validate = (): boolean => {
    const newErrors: Partial<CreateProjectRequest> = {}
    if (!formData.name.trim()) {
      newErrors.name = '项目名称不能为空'
    }
    if (formData.repo_url && !formData.repo_url.match(/^https?:\/\/.+/)) {
      newErrors.repo_url = '请输入有效的仓库 URL'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    setIsSubmitting(true)
    try {
      await onSubmit(formData)
      setFormData({ name: '', description: '', repo_url: '' })
      onClose()
    } catch (error) {
      console.error('Failed to create project:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name as keyof CreateProjectRequest]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">创建新项目</h2>
          <p className="text-sm text-gray-500 mt-1">
            填写项目信息以创建新的运维项目
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
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="例如：用户服务系统"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.name && (
                <p className="mt-1 text-xs text-red-500">{errors.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                项目描述
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="简要描述项目的功能和用途..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                仓库地址
              </label>
              <input
                type="text"
                name="repo_url"
                value={formData.repo_url}
                onChange={handleChange}
                placeholder="https://github.com/your-org/your-repo"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 ${
                  errors.repo_url ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.repo_url && (
                <p className="mt-1 text-xs text-red-500">{errors.repo_url}</p>
              )}
            </div>
          </div>

          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? '创建中...' : '创建项目'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
