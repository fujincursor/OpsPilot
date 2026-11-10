import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export interface ReviewCardData {
  reviewId: string
  itemType: string
  title: string
  status: string
  summary: string
  rootCause?: string
  files?: string[]
  dueAt?: string
}

export interface Message {
  id: string
  type: 'user' | 'agent'
  content: string
  sender: string
  timestamp: string
  agentType?: 'lead' | 'bugfix' | 'feature'
  status?: 'analyzing' | 'complete' | 'error'
  knowledgeResults?: KnowledgeResult[]
  classifyResult?: ClassifyResult
  agentSteps?: AgentStep[]
  progress?: number
  review?: ReviewCardData
  knowledgeProjectId?: string
}

interface KnowledgeResult {
  title: string
  relevance: number
  snippet: string
}

interface ClassifyResult {
  type: 'bug' | 'feature' | 'question'
  priority: 'high' | 'medium' | 'low'
  ticketId?: string
}

interface AgentStep {
  id: number
  name: string
  status: 'done' | 'running' | 'pending'
}

interface MessageListProps {
  messages: Message[]
  isLoading?: boolean
  onDecide?: (reviewId: string, decision: 'approve' | 'reject' | 'revision', reason: string) => Promise<void>
  onOpenKnowledge?: (projectId: string) => void
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}

function ApprovalCard({
  review,
  onDecide,
}: {
  review: ReviewCardData
  onDecide?: MessageListProps['onDecide']
}) {
  const [reason, setReason] = useState('')
  const [mode, setMode] = useState<'reject' | 'revision' | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const pending = review.status === 'pending' || review.status === 'in_review'
  const overdue = Boolean(review.dueAt) && pending && new Date(review.dueAt || '') < new Date()
  const border = overdue || review.status === 'rejected'
    ? 'border-red-300 bg-red-50'
    : review.status === 'approved'
      ? 'border-green-300 bg-green-50'
      : review.status === 'revision_requested'
        ? 'border-orange-300 bg-orange-50'
        : 'border-amber-200 bg-amber-50'
  const statusText: Record<string, string> = {
    pending: '待审批',
    in_review: '审批中',
    approved: '已通过',
    rejected: '已拒绝',
    revision_requested: '已要求修改',
  }

  const submit = async (decision: 'approve' | 'reject' | 'revision') => {
    if (!onDecide) return
    setSubmitting(true)
    setError('')
    try {
      await onDecide(review.reviewId, decision, reason.trim())
      setMode(null)
      setReason('')
    } catch (decideError) {
      setError(decideError instanceof Error ? decideError.message : '审批失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={`mt-3 rounded-lg border p-3.5 ${border}`}>
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-sm font-semibold text-gray-800">{review.title}</span>
        <span className={`text-xs font-medium ${overdue ? 'text-red-700' : 'text-gray-700'}`}>
          {overdue ? '已超时' : statusText[review.status] || review.status}
        </span>
      </div>
      {review.rootCause && (
        <p className="mb-2 text-xs text-gray-700">根因：{review.rootCause}</p>
      )}
      {review.files && review.files.length > 0 && (
        <ul className="mb-2 space-y-1 text-xs text-gray-600">
          {review.files.map((file) => (
            <li key={file} className="font-mono">{file}</li>
          ))}
        </ul>
      )}
      {review.summary && (
        <div className="mb-3 max-h-40 overflow-y-auto whitespace-pre-wrap text-xs leading-relaxed text-gray-600">
          {review.summary}
        </div>
      )}
      {pending && onDecide && (
        <div className="space-y-2">
          {mode && (
            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder={mode === 'reject' ? '请填写拒绝原因' : '请填写修改意见'}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
              rows={3}
            />
          )}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={submitting}
              onClick={() => submit('approve')}
              className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
            >
              通过
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={() => (mode === 'revision' && reason.trim() ? submit('revision') : setMode('revision'))}
              className="rounded-md bg-white px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-200"
            >
              驳回修订
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={() => (mode === 'reject' && reason.trim() ? submit('reject') : setMode('reject'))}
              className="rounded-md bg-white px-3 py-1.5 text-xs font-medium text-red-600 border border-red-200"
            >
              拒绝并关闭
            </button>
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
        </div>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-1 py-2">
      <span className="w-2 h-2 rounded-full bg-primary typing-dot"></span>
      <span className="w-2 h-2 rounded-full bg-primary typing-dot"></span>
      <span className="w-2 h-2 rounded-full bg-primary typing-dot"></span>
    </div>
  )
}

function KnowledgeCard({ results }: { results: KnowledgeResult[] }) {
  return (
    <div className="mt-3 bg-gray-50 rounded-lg overflow-hidden">
      <div className="px-3.5 py-2.5 bg-white border-b border-gray-200 flex items-center justify-between text-sm font-semibold text-gray-800">
        <span>📚 知识检索结果</span>
        <span className="text-xs text-primary cursor-pointer">收起 ▲</span>
      </div>
      <div className="p-3 space-y-2">
        {results.map((item, index) => (
          <div key={index} className="p-3 bg-white rounded-md border border-gray-200">
            <div className="flex items-center justify-between text-sm font-medium text-gray-800 mb-1.5">
              <span className="flex items-center gap-1.5">📄 {item.title}</span>
              <span className="text-xs text-green-600">相关度 {item.relevance}%</span>
            </div>
            <div className="text-xs text-gray-500 leading-relaxed">
              <MarkdownContent content={item.snippet} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ClassifyCard({ result }: { result: ClassifyResult }) {
  const typeConfig = {
    bug: { emoji: '🐛', text: 'Bug', className: 'text-red-500' },
    feature: { emoji: '✨', text: '需求', className: 'text-blue-500' },
    question: { emoji: '❓', text: '问题', className: 'text-gray-500' },
  }

  const priorityConfig = {
    high: { emoji: '🔴', text: '高', className: 'text-red-500' },
    medium: { emoji: '🟡', text: '中', className: 'text-amber-500' },
    low: { emoji: '🟢', text: '低', className: 'text-green-500' },
  }

  const type = typeConfig[result.type]
  const priority = priorityConfig[result.priority]

  return (
    <div className="mt-3 bg-gray-50 rounded-lg p-3.5">
      <div className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-1.5">
        🏷️ 需求分类结果
      </div>
      <div className="flex gap-3 flex-wrap">
        <div className="px-3.5 py-2 bg-white border border-gray-200 rounded-md">
          <div className="text-[11px] text-gray-400 mb-0.5">类型</div>
          <div className={`text-sm font-semibold ${type.className}`}>
            {type.emoji} {type.text}
          </div>
        </div>
        <div className="px-3.5 py-2 bg-white border border-gray-200 rounded-md">
          <div className="text-[11px] text-gray-400 mb-0.5">优先级</div>
          <div className={`text-sm font-semibold ${priority.className}`}>
            {priority.emoji} {priority.text}
          </div>
        </div>
        {result.ticketId && (
          <div className="px-3.5 py-2 bg-white border border-gray-200 rounded-md">
            <div className="text-[11px] text-gray-400 mb-0.5">工单编号</div>
            <div className="text-sm font-semibold text-gray-800">{result.ticketId}</div>
          </div>
        )}
      </div>
    </div>
  )
}

function AgentStepsCard({ steps, progress }: { steps: AgentStep[]; progress?: number }) {
  const stepIconConfig = {
    done: { className: 'bg-green-100 text-green-600', icon: '✓' },
    running: { className: 'bg-primary-light text-primary', icon: '◉' },
    pending: { className: 'bg-gray-50 text-gray-400 border border-gray-200', icon: '○' },
  }

  return (
    <div className="mt-3 bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2.5">
        <span className="w-7 h-7 rounded-md bg-primary-light flex items-center justify-center text-sm">
          🔧
        </span>
        <span className="text-sm font-semibold text-gray-800">执行步骤</span>
      </div>
      <div className="p-4">
        <ul className="space-y-2">
          {steps.map((step) => {
            const config = stepIconConfig[step.status]
            return (
              <li
                key={step.id}
                className={`flex items-center gap-2.5 py-2 text-sm ${
                  step.status === 'running' ? 'text-gray-800 font-medium' : 'text-gray-500'
                }`}
              >
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${config.className}`}>
                  {config.icon}
                </span>
                {step.id}. {step.name}
              </li>
            )
          })}
        </ul>
        {progress !== undefined && (
          <div className="mt-3">
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-indigo-500 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-400 mt-1.5 text-right">{progress}%</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function MessageList({ messages, isLoading, onDecide, onOpenKnowledge }: MessageListProps) {
  const agentConfig = {
    lead: { emoji: '🤖', name: 'Lead Agent' },
    bugfix: { emoji: '🔧', name: 'Bug Fix Agent' },
    feature: { emoji: '✨', name: 'Feature Agent' },
  }

  return (
    <div className="space-y-5">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex flex-col ${message.type === 'user' ? 'items-end' : 'items-start'}`}
        >
          <div
            className={`max-w-[85%] px-4 py-3.5 rounded-xl relative ${
              message.type === 'user'
                ? 'bg-primary-light rounded-tr-sm'
                : 'bg-white border border-gray-200 rounded-tl-sm shadow-sm'
            }`}
          >
            {message.type === 'agent' && (
              <div className="flex items-center gap-2 mb-2.5 pb-2.5 border-b border-gray-200">
                <span className="w-6 h-6 rounded-full bg-primary-light flex items-center justify-center text-sm">
                  {agentConfig[message.agentType || 'lead'].emoji}
                </span>
                <span className="text-sm font-semibold text-gray-800">
                  {agentConfig[message.agentType || 'lead'].name}
                </span>
                {message.status && (
                  <span className={`ml-auto text-xs flex items-center gap-1.5 ${
                    message.status === 'analyzing'
                      ? 'text-primary'
                      : message.status === 'error'
                        ? 'text-red-500'
                        : 'text-gray-400'
                  }`}>
                    {message.status === 'analyzing' && <TypingIndicator />}
                    {message.status === 'analyzing'
                      ? '执行中...'
                      : message.status === 'error'
                        ? '未完成'
                        : '分析完成 ✓'}
                  </span>
                )}
              </div>
            )}

            <div className="text-sm leading-relaxed text-gray-800">
              {message.type === 'agent' ? (
                <MarkdownContent content={message.content} />
              ) : (
                <p className="whitespace-pre-wrap">{message.content}</p>
              )}
            </div>

            {message.knowledgeResults && message.knowledgeResults.length > 0 && (
              <KnowledgeCard results={message.knowledgeResults} />
            )}

            {message.classifyResult && (
              <ClassifyCard result={message.classifyResult} />
            )}

            {message.review && (
              <ApprovalCard review={message.review} onDecide={onDecide} />
            )}

            {message.knowledgeProjectId && onOpenKnowledge && (
              <button
                type="button"
                onClick={() => onOpenKnowledge(message.knowledgeProjectId as string)}
                className="mt-3 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-white"
              >
                去补齐知识库
              </button>
            )}

            {message.agentSteps && message.agentSteps.length > 0 && (
              <AgentStepsCard steps={message.agentSteps} progress={message.progress} />
            )}

            <div className="text-[11px] text-gray-400 mt-2">
              {message.type === 'user' ? '👤' : agentConfig[message.agentType || 'lead'].emoji}{' '}
              {message.sender} · {message.timestamp}
            </div>
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="flex items-start">
          <div className="max-w-[85%] px-4 py-3.5 rounded-xl rounded-tl-sm bg-white border border-gray-200 shadow-sm">
            <div className="flex items-center gap-2 mb-2.5 pb-2.5 border-b border-gray-200">
              <span className="w-6 h-6 rounded-full bg-primary-light flex items-center justify-center text-sm">
                🤖
              </span>
              <span className="text-sm font-semibold text-gray-800">Lead Agent</span>
            </div>
            <TypingIndicator />
          </div>
        </div>
      )}
    </div>
  )
}
