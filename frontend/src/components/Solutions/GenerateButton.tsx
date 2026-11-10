interface GenerateButtonProps {
  onClick: () => void
  isLoading?: boolean
  disabled?: boolean
  label?: string
}

export default function GenerateButton({
  onClick,
  isLoading = false,
  disabled = false,
  label = '生成方案',
}: GenerateButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading || disabled}
      className={`
        inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
        transition-all duration-200
        ${isLoading || disabled
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
          : 'bg-gradient-to-r from-primary to-blue-600 text-white hover:from-primary-hover hover:to-blue-700 shadow-md hover:shadow-lg'
        }
      `}
    >
      {isLoading ? (
        <>
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          <span>生成中...</span>
        </>
      ) : (
        <>
          <span>🤖</span>
          <span>{label}</span>
        </>
      )}
    </button>
  )
}
