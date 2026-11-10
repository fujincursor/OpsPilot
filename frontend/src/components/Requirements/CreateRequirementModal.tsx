import { useState, useEffect, useCallback } from 'react'
import type {
  CreateRequirementRequest,
  AnalysisResult,
  RequirementType,
  RequirementPriority,
} from '../../types'
import { requirementService } from '../../services'
import TypeIcon from './TypeIcon'
import PriorityBadge from './PriorityBadge'
import AnalysisCard from './AnalysisCard'

interface CreateRequirementModalProps {
  isOpen: boolean
  projectId: string
  onClose: () => void
  onSubmit: (data: CreateRequirementRequest) => Promise<void>
}

export default function CreateRequirementModal({
  isOpen,
  projectId: _projectId,
  onClose,
  onSubmit,
}: CreateRequirementModalProps) {
  void _projectId
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [source, setSource] = useState('')
  const [type, setType] = useState<RequirementType>('feature')
  const [priority, setPriority] = useState<RequirementPriority>('medium')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [useAiSuggestion, setUseAiSuggestion] = useState(true)

  const analyzeText = useCallback(async (text: string) => {
    if (text.length < 10) {
      setAnalysisResult(null)
      return
    }

    setIsAnalyzing(true)
    try {
      const result = await requirementService.analyzeText(text)
      setAnalysisResult(result)
      if (useAiSuggestion) {
        setType(result.type)
        setPriority(result.priority)
      }
    } catch (error) {
      console.error(error)
      setAnalysisResult(null)
    } finally {
      setIsAnalyzing(false)
    }
  }, [useAiSuggestion])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (description) {
        analyzeText(description)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [description, analyzeText])

  useEffect(() => {
    if (!isOpen) {
      setTitle('')
      setDescription('')
      setSource('')
      setType('feature')
      setPriority('medium')
      setAnalysisResult(null)
    }
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !description.trim()) return

    setIsSubmitting(true)
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim(),
        source: source.trim() || undefined,
        type,
        priority,
      })
      onClose()
    } catch (error) {
      console.error('Failed to create requirement:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  const types: RequirementType[] = ['bug', 'feature', 'question']
  const priorities: RequirementPriority[] = ['low', 'medium', 'high', 'critical']

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-800">创建新需求</h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                需求标题 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="简要描述需求内容"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                详细描述 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="详细描述需求背景、目标和预期效果..."
                rows={4}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors resize-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                需求来源
              </label>
              <input
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="如：工单 #123、用户反馈、产品规划等"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
              />
            </div>

            {(isAnalyzing || analysisResult) && (
              <div className="py-2">
                <AnalysisCard analysis={analysisResult!} isLoading={isAnalyzing} />
                {analysisResult && (
                  <label className="flex items-center gap-2 mt-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useAiSuggestion}
                      onChange={(e) => {
                        setUseAiSuggestion(e.target.checked)
                        if (e.target.checked && analysisResult) {
                          setType(analysisResult.type)
                          setPriority(analysisResult.priority)
                        }
                      }}
                      className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                    />
                    <span className="text-sm text-gray-600">采用 AI 建议的类型和优先级</span>
                  </label>
                )}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  需求类型
                </label>
                <div className="flex flex-wrap gap-2">
                  {types.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setType(t)}
                      className={`transition-all ${
                        type === t
                          ? 'ring-2 ring-primary ring-offset-1'
                          : 'opacity-60 hover:opacity-100'
                      }`}
                    >
                      <TypeIcon type={t} showLabel />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  优先级
                </label>
                <div className="flex flex-wrap gap-2">
                  {priorities.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPriority(p)}
                      className={`transition-all ${
                        priority === p
                          ? 'ring-2 ring-primary ring-offset-1'
                          : 'opacity-60 hover:opacity-100'
                      }`}
                    >
                      <PriorityBadge priority={p} />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim() || !description.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              {isSubmitting ? '创建中...' : '创建需求'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
