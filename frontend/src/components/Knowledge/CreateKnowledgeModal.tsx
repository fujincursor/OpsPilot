import { useState } from 'react'
import type { CreateKnowledgeBaseRequest, KnowledgeType } from '../../types'

interface CreateKnowledgeModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CreateKnowledgeBaseRequest) => Promise<void>
}

const typeOptions: { value: KnowledgeType; label: string; icon: string; desc: string }[] = [
  { value: 'doc', label: '文档', icon: '📄', desc: '技术文档、设计文档、需求文档等' },
  { value: 'code', label: '代码', icon: '💻', desc: '代码仓库、代码片段、示例代码等' },
  { value: 'faq', label: 'FAQ', icon: '❓', desc: '常见问题、故障排查手册等' },
]

export default function CreateKnowledgeModal({
  isOpen,
  onClose,
  onSubmit,
}: CreateKnowledgeModalProps) {
  const [formData, setFormData] = useState<CreateKnowledgeBaseRequest>({
    name: '',
    description: '',
    type: 'doc',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<Partial<Record<keyof CreateKnowledgeBaseRequest, string>>>({})

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof CreateKnowledgeBaseRequest, string>> = {}
    if (!formData.name.trim()) {
      newErrors.name = '知识库名称不能为空'
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
      setFormData({ name: '', description: '', type: 'doc' })
      onClose()
    } catch (error) {
      console.error('Failed to create knowledge base:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name as keyof CreateKnowledgeBaseRequest]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">创建知识库</h2>
          <p className="text-sm text-gray-500 mt-1">
            创建新的知识库来管理项目相关文档
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                知识库名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="例如：运维手册"
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
                知识库类型
              </label>
              <div className="grid grid-cols-3 gap-3">
                {typeOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() =>
                      setFormData((prev) => ({ ...prev, type: option.value }))
                    }
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      formData.type === option.value
                        ? 'border-primary bg-primary-light'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">{option.icon}</div>
                    <div className="text-sm font-medium text-gray-800">
                      {option.label}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                      {option.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                描述
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="简要描述知识库的内容和用途..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              />
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
              {isSubmitting ? '创建中...' : '创建知识库'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
