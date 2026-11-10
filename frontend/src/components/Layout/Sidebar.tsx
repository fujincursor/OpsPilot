import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

interface Session {
  id: string
  title: string
  status: 'running' | 'pending' | 'complete'
  ticketId: string
  date: string
}

interface SidebarProps {
  currentProject?: string
  sessions?: Session[]
}

const mockSessions: Session[] = [
  {
    id: '1',
    title: '数据库连接超时问题',
    status: 'running',
    ticketId: 'BUG-2024-001',
    date: '今天',
  },
  {
    id: '2',
    title: '用户权限模块设计',
    status: 'pending',
    ticketId: 'FEAT-2024-003',
    date: '今天',
  },
  {
    id: '3',
    title: 'API 响应优化',
    status: 'complete',
    ticketId: 'BUG-2024-002',
    date: '昨天',
  },
]

export default function Sidebar({ currentProject = '项目 Alpha', sessions = mockSessions }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const [selectedSession, setSelectedSession] = useState<string | null>(null)

  const statusConfig = {
    running: { className: 'bg-blue-100 text-blue-600', text: '进行中' },
    pending: { className: 'bg-amber-100 text-amber-600', text: '待审批' },
    complete: { className: 'bg-green-100 text-green-600', text: '已完成' },
  }

  const groupedSessions = sessions.reduce((acc, session) => {
    if (!acc[session.date]) {
      acc[session.date] = []
    }
    acc[session.date].push(session)
    return acc
  }, {} as Record<string, Session[]>)

  const handleSessionClick = (sessionId: string) => {
    setSelectedSession(sessionId)
    navigate(`/chat/${sessionId}`)
  }

  const handleNewSession = () => {
    setSelectedSession(null)
    navigate('/chat')
  }

  const isActive = (sessionId: string) => {
    return location.pathname === `/chat/${sessionId}` || selectedSession === sessionId
  }

  return (
    <aside className="w-[280px] bg-white border-r border-gray-200 flex flex-col flex-shrink-0 h-full">
      {/* Project Selector */}
      <div className="p-4 border-b border-gray-200">
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          当前项目
        </div>
        <div
          onClick={() => navigate('/projects')}
          className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-primary-light transition-colors"
        >
          <div className="flex items-center justify-between text-sm font-semibold text-gray-800">
            <span>🏢 {currentProject}</span>
            <span className="text-gray-400">▼</span>
          </div>
          <div className="mt-2 space-y-1">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              知识库: 就绪
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Agent: 已配置
            </div>
          </div>
        </div>
        <button
          onClick={() => navigate('/projects')}
          className="w-full mt-3 py-2 text-sm text-primary hover:text-primary-hover font-medium flex items-center justify-center gap-1.5 bg-primary-light hover:bg-primary/20 rounded-lg transition-colors"
        >
          📁 项目管理
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-2">
        {Object.entries(groupedSessions).map(([date, dateSessions]) => (
          <div key={date} className="mb-4">
            <div className="px-2 py-1 text-xs font-semibold text-gray-400 flex items-center gap-1">
              📌 {date}
            </div>
            {dateSessions.map((session) => (
              <div
                key={session.id}
                onClick={() => handleSessionClick(session.id)}
                className={`p-3 rounded-md cursor-pointer transition-colors mb-0.5 ${
                  isActive(session.id)
                    ? 'bg-primary-light'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="text-sm font-medium text-gray-800 truncate">
                  {session.title}
                </div>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${statusConfig[session.status].className}`}>
                    {statusConfig[session.status].text}
                  </span>
                  <span>{session.ticketId}</span>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* New Session Button */}
      <div className="p-4">
        <button
          onClick={handleNewSession}
          className="w-full py-3 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
        >
          ➕ 开始新会话
        </button>
      </div>
    </aside>
  )
}
