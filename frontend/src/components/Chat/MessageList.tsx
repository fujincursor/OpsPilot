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
}

interface KnowledgeResult {
  title: string
  relevance: number
  snippet: string
}

interface ClassifyResult {
  type: 'bug' | 'feature' | 'question'
  priority: 'high' | 'medium' | 'low'
  ticketId: string
}

interface AgentStep {
  id: number
  name: string
  status: 'done' | 'running' | 'pending'
}

interface MessageListProps {
  messages: Message[]
  isLoading?: boolean
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
            <p className="text-xs text-gray-500 leading-relaxed">{item.snippet}</p>
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
        <div className="px-3.5 py-2 bg-white border border-gray-200 rounded-md">
          <div className="text-[11px] text-gray-400 mb-0.5">工单编号</div>
          <div className="text-sm font-semibold text-gray-800">{result.ticketId}</div>
        </div>
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

export default function MessageList({ messages, isLoading }: MessageListProps) {
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
                    message.status === 'analyzing' ? 'text-primary' : 'text-gray-400'
                  }`}>
                    {message.status === 'analyzing' && <TypingIndicator />}
                    {message.status === 'analyzing' ? '执行中...' : '分析完成 ✓'}
                  </span>
                )}
              </div>
            )}

            <div className="text-sm leading-relaxed text-gray-800">
              {message.content}
            </div>

            {message.knowledgeResults && message.knowledgeResults.length > 0 && (
              <KnowledgeCard results={message.knowledgeResults} />
            )}

            {message.classifyResult && (
              <ClassifyCard result={message.classifyResult} />
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
