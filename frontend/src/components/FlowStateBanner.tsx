interface FlowStateBannerProps {
  mode: 'running' | 'failed'
  title: string
  detail?: string
  onRetry?: () => void
  retryLabel?: string
}

export default function FlowStateBanner({ mode, title, detail, onRetry, retryLabel = '重试' }: FlowStateBannerProps) {
  const failed = mode === 'failed'
  return (
    <div className={`mb-4 rounded-xl border p-4 ${failed ? 'border-red-200 bg-red-50' : 'border-blue-200 bg-blue-50'}`}>
      <div className={`text-sm font-medium ${failed ? 'text-red-800' : 'text-blue-800'}`}>{title}</div>
      {detail && <p className="mt-1 whitespace-pre-wrap text-sm text-gray-600">{detail}</p>}
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-3 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm">
          {retryLabel}
        </button>
      )}
    </div>
  )
}
