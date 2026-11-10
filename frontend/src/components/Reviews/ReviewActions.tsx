interface ReviewActionsProps {
  onApprove: () => void
  onReject: () => void
  onRequestRevision: () => void
  disabled?: boolean
}

export default function ReviewActions({
  onApprove,
  onReject,
  onRequestRevision,
  disabled = false,
}: ReviewActionsProps) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onApprove}
        disabled={disabled}
        className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
      >
        ✓ 通过
      </button>
      <button
        onClick={onRequestRevision}
        disabled={disabled}
        className="px-4 py-2 bg-orange-500 hover:bg-orange-600 disabled:bg-orange-300 text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
      >
        ↻ 要求修改
      </button>
      <button
        onClick={onReject}
        disabled={disabled}
        className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
      >
        ✕ 拒绝
      </button>
    </div>
  )
}
