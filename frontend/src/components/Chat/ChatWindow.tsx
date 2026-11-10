import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import MessageList, { Message } from './MessageList'
import MessageInput from './MessageInput'
import api from '../../services/api'
import { authService } from '../../services/authService'
import { chatService, toChatMessages } from '../../services/chatService'
import { reviewService } from '../../services/reviewService'

interface QuickAction {
  emoji: string
  text: string
  value: string
  placeholder: string
}

interface ChatWindowProps {
  sessionId?: string
  initialMessages?: Message[]
  projectId?: string
  projectName?: string
  onSessionReady?: (sessionId: string) => void
}

interface ChatResponse {
  success: boolean
  message: string
  thread_id?: string
  data?: {
    knowledge_results?: Array<{
      title: string
      snippet: string
      score: number
    }>
    classification?: {
      type: 'bug' | 'feature' | 'question'
      priority: 'high' | 'medium' | 'low'
      title?: string
      ticket_id?: string
    }
    knowledge_ready?: boolean
    project_id?: string
  }
}

const quickActions: QuickAction[] = [
  { emoji: '🐛', text: '报告 Bug', value: '我遇到了一个 Bug：', placeholder: '请描述出错现象、复现步骤和影响范围...' },
  { emoji: '✨', text: '提需求', value: '我有一个新需求：', placeholder: '请描述希望新增或改进的功能...' },
  { emoji: '❓', text: '咨询问题', value: '我想咨询一个问题：', placeholder: '请写出想了解的问题...' },
]

export default function ChatWindow({
  sessionId,
  initialMessages = [],
  projectId,
  projectName = '未选择项目',
  onSessionReady,
}: ChatWindowProps) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(Boolean(sessionId))
  const [historyError, setHistoryError] = useState('')
  const [prefillText, setPrefillText] = useState('')
  const [prefillToken, setPrefillToken] = useState(0)
  const [inputPlaceholder, setInputPlaceholder] = useState('请描述您遇到的问题或需求...')
  const messageAreaRef = useRef<HTMLDivElement>(null)
  const skipReloadRef = useRef<string | null>(null)

  const isNewSession = !sessionId && messages.length === 0 && !isLoading

  useEffect(() => {
    if (!sessionId) {
      setHistoryLoading(false)
      setHistoryError('')
      setMessages([])
      return
    }
    if (skipReloadRef.current === sessionId) {
      skipReloadRef.current = null
      setHistoryLoading(false)
      return
    }
    let active = true
    setHistoryLoading(true)
    setHistoryError('')
    chatService.getSession(sessionId)
      .then((session) => {
        if (active) setMessages(toChatMessages(session.messages, session.project_id))
      })
      .catch(() => {
        if (active) {
          setMessages([])
          setHistoryError('对话记录加载失败')
        }
      })
      .finally(() => {
        if (active) setHistoryLoading(false)
      })
    return () => {
      active = false
    }
  }, [sessionId])

  useEffect(() => {
    if (messageAreaRef.current) {
      messageAreaRef.current.scrollTop = messageAreaRef.current.scrollHeight
    }
  }, [messages, historyLoading])

  const handleSendMessage = async (content: string) => {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    const newUserMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      sender: authService.getUser()?.username || '我',
      timestamp,
    }

    setMessages((prev) => [...prev, newUserMessage])
    setIsLoading(true)

    try {
      const response = await api.post<ChatResponse>('/deerflow/chat', {
        message: content,
        thread_id: sessionId,
        project_id: projectId,
        sender: authService.getUser()?.username || '我',
      }, { timeout: 120000 })
      const knowledgeResults = (response.data.data?.knowledge_results || []).map((item) => ({
        title: item.title,
        snippet: item.snippet,
        relevance: Math.round(item.score * 100),
      }))
      const classification = response.data.data?.classification
      const agentResponse: Message = {
        id: `agent-${Date.now()}`,
        type: 'agent',
        content: response.data.message,
        sender: 'Lead Agent',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        agentType: 'lead',
        status: response.data.success ? 'complete' : 'error',
        knowledgeResults,
        classifyResult: classification
          ? {
              type: classification.type,
              priority: classification.priority,
              ticketId: classification.ticket_id || '',
            }
          : undefined,
        knowledgeProjectId: response.data.data?.knowledge_ready === false ? projectId : undefined,
      }
      if (response.data.thread_id) {
        const session = await chatService.getSession(response.data.thread_id)
        setMessages(toChatMessages(session.messages, session.project_id))
        skipReloadRef.current = response.data.thread_id
        onSessionReady?.(response.data.thread_id)
      } else {
        setMessages((prev) => [...prev, agentResponse])
      }
    } catch {
      const agentResponse: Message = {
        id: `agent-${Date.now()}`,
        type: 'agent',
        content: '对话请求失败',
        sender: 'Lead Agent',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        agentType: 'lead',
        status: 'error',
      }
      setMessages((prev) => [...prev, agentResponse])
    } finally {
      setIsLoading(false)
    }
  }

  const handleDecide = async (
    reviewId: string,
    decision: 'approve' | 'reject' | 'revision',
    reason: string
  ) => {
    if (decision === 'approve') {
      await reviewService.approve(reviewId, reason)
    } else if (decision === 'reject') {
      await reviewService.reject(reviewId, reason)
    } else {
      await reviewService.requestRevision(reviewId, reason)
    }
    if (sessionId) {
      const session = await chatService.getSession(sessionId)
      setMessages(toChatMessages(session.messages, session.project_id))
    }
  }

  const handleQuickAction = (action: QuickAction) => {
    setPrefillText(action.value)
    setPrefillToken(Date.now())
    setInputPlaceholder(action.placeholder)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message Area */}
      <div ref={messageAreaRef} className="flex-1 overflow-y-auto p-6">
        <div className="max-w-[900px] mx-auto">
          {historyLoading ? (
            <div className="text-center py-16 text-sm text-gray-500">正在加载对话...</div>
          ) : historyError ? (
            <div className="text-center py-16 text-sm text-red-500">{historyError}</div>
          ) : isNewSession ? (
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
            <MessageList
              messages={messages}
              isLoading={isLoading}
              onDecide={handleDecide}
              onOpenKnowledge={(id) => navigate(`/projects/${id}/knowledge`)}
            />
          )}
        </div>
      </div>

      {/* Input Area */}
      <MessageInput
        onSend={handleSendMessage}
        disabled={isLoading || historyLoading}
        placeholder={inputPlaceholder}
        prefillText={prefillText}
        prefillToken={prefillToken}
      />
    </div>
  )
}
