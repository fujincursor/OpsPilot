import { useState } from 'react'

type DecisionType = 'approve' | 'reject' | 'revision'

interface DecisionModalProps {
  isOpen: boolean
  type: DecisionType
  onClose: () => void
  onConfirm: (reason: string) => Promise<void>
}

const modalConfig: Record<DecisionType, {
  title: string
  placeholder: string
  confirmText: string
  confirmClass: string
}> = {
  approve: {
    title: '确认通过',
    placeholder: '请输入通过原因（可选）...',
    confirmText: '确认通过',
    confirmClass: 'bg-green-600 hover:bg-green-700',
  },
  reject: {
    title: '确认拒绝',
    placeholder: '请输入拒绝原因（必填）...',
    confirmText: '确认拒绝',
    confirmClass: 'bg-red-600 hover:bg-red-700',
  },
  revision: {
    title: '要求修改',
    placeholder: '请输入需要修改的内容说明（必填）...',
    confirmText: '提交修改要求',
    confirmClass: 'bg-orange-500 hover:bg-orange-600',
  },
}

export default function DecisionModal({
  isOpen,
  type,
  onClose,
  onConfirm,
}: DecisionModalProps) {
  const [reason, setReason] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const config = modalConfig[type]
  const isRequired = type !== 'approve'
  const canSubmit = type === 'approve' || reason.trim().length > 0

  const handleConfirm = async () => {
    if (!canSubmit || isSubmitting) return
    setIsSubmitting(true)
    try {
      await onConfirm(reason.trim() || '通过')
      setReason('')
      onClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (isSubmitting) return
    setReason('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div
        className="bg-white rounded-xl w-full max-w-md mx-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800">{config.title}</h2>
        </div>

        <div className="p-6">
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder={config.placeholder}
            rows={4}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"
            autoFocus
          />
          {isRequired && !reason.trim() && (
            <p className="mt-2 text-xs text-red-500">此字段为必填项</p>
          )}
        </div>

        <div className="p-4 bg-gray-50 rounded-b-xl flex justify-end gap-3">
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleConfirm}
            disabled={!canSubmit || isSubmitting}
            className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-50 ${config.confirmClass}`}
          >
            {isSubmitting ? '提交中...' : config.confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
