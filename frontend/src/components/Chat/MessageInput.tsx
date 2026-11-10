import { useState, useRef, useEffect, KeyboardEvent } from 'react'

interface MessageInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export default function MessageInput({
  onSend,
  disabled = false,
  placeholder = '请描述您遇到的问题或需求...',
}: MessageInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [message])

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="p-4 md:p-6 bg-white border-t border-gray-200">
      <div className="max-w-[900px] mx-auto">
        <div
          className={`flex items-end gap-3 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 transition-all ${
            !disabled ? 'focus-within:border-primary focus-within:ring-4 focus-within:ring-primary-light' : ''
          }`}
        >
          {/* Action Buttons */}
          <div className="flex gap-1">
            <button
              className="w-8 h-8 rounded-md flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary-light transition-colors"
              title="上传附件"
            >
              📎
            </button>
            <button
              className="w-8 h-8 rounded-md flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary-light transition-colors"
              title="上传截图"
            >
              📷
            </button>
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="flex-1 bg-transparent border-none resize-none text-sm leading-relaxed text-gray-800 placeholder-gray-400 focus:outline-none disabled:opacity-50 min-h-[24px] max-h-[120px]"
          />

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            className="px-5 py-2 bg-primary hover:bg-primary-hover disabled:bg-gray-200 disabled:cursor-not-allowed text-white rounded-md text-sm font-medium flex items-center gap-1.5 transition-colors"
          >
            发送 ➤
          </button>
        </div>

        <div className="text-center text-xs text-gray-400 mt-2">
          💡 按 Enter 发送，Shift+Enter 换行
        </div>
      </div>
    </div>
  )
}
