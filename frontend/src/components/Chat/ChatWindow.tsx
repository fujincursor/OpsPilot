import { useState, useRef, useEffect, useCallback } from 'react'
import MessageList, { Message } from './MessageList'
import MessageInput from './MessageInput'
import { deerflowService, AgentStatus } from '../../services/deerflowService'

interface QuickAction {
  emoji: string
  text: string
  value: string
}

interface ChatWindowProps {
  sessionId?: string
  initialMessages?: Message[]
  projectName?: string
}

const quickActions: QuickAction[] = [
  { emoji: '🐛', text: '报告 Bug', value: '我遇到了一个 Bug：' },
  { emoji: '✨', text: '提需求', value: '我有一个新需求：' },
  { emoji: '❓', text: '咨询问题', value: '我想咨询一个问题：' },
]

export default function ChatWindow({
  sessionId,
  initialMessages = [],
  projectName = '项目 Alpha',
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [threadId, setThreadId] = useState<string | undefined>(sessionId)
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null)
  const messageAreaRef = useRef<HTMLDivElement>(null)

  const isNewSession = !sessionId && messages.length === 0

  useEffect(() => {
    deerflowService.getStatus().then(setAgentStatus).catch(console.error)
  }, [])

  useEffect(() => {
    if (messageAreaRef.current) {
      messageAreaRef.current.scrollTop = messageAreaRef.current.scrollHeight
    }
  }, [messages])

  const handleSendMessage = useCallback(async (content: string) => {
    const newUserMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      sender: '张三',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, newUserMessage])
    setIsLoading(true)

    try {
      const response = await deerflowService.chat({
        message: content,
        thread_id: threadId,
        context: { project_name: projectName }
      })

      if (response.thread_id) {
        setThreadId(response.thread_id)
      }

      const modeIndicator = response.data?.mode === 'mock' ? ' [模拟模式]' : ''
      
      const agentResponse: Message = {
        id: `agent-${Date.now()}`,
        type: 'agent',
        content: response.message + modeIndicator,
        sender: 'Lead Agent',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        agentType: 'lead',
        status: response.success ? 'complete' : 'error',
      }
      setMessages((prev) => [...prev, agentResponse])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: 'agent',
        content: `抱歉，发生错误：${error instanceof Error ? error.message : '未知错误'}`,
        sender: 'System',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        agentType: 'lead',
        status: 'error',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [threadId, projectName])

  const handleQuickAction = (action: QuickAction) => {
    handleSendMessage(action.value)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message Area */}
      <div ref={messageAreaRef} className="flex-1 overflow-y-auto p-6">
        <div className="max-w-[900px] mx-auto">
          {isNewSession ? (
            /* Welcome Screen */
            <div className="text-center py-16">
              <div className="w-16 h-16 bg-primary-light rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">
                🤖
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                运维 Agent · {projectName}
              </h2>
              <p className="text-sm text-gray-500 leading-relaxed max-w-md mx-auto mb-6">
                您好！我是{projectName}的智能运维助手。
                <br />
                我可以帮您处理 Bug 修复、需求分析、代码生成等任务。
              </p>

              <ol className="text-left max-w-xs mx-auto text-sm text-gray-500 mb-6 space-y-2">
                <li>1️⃣ 自动检索相关知识库</li>
                <li>2️⃣ 分析并分类您的需求</li>
                <li>3️⃣ 生成解决方案并提交审批</li>
              </ol>

              <div className="flex justify-center gap-3 flex-wrap">
                {quickActions.map((action) => (
                  <button
                    key={action.text}
                    onClick={() => handleQuickAction(action)}
                    className="px-5 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-800 flex items-center gap-2 hover:border-primary hover:bg-primary-light transition-colors"
                  >
                    {action.emoji} {action.text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <MessageList messages={messages} isLoading={isLoading} />
          )}
        </div>
      </div>

      {/* Input Area */}
      <MessageInput onSend={handleSendMessage} disabled={isLoading} />
    </div>
  )
}
