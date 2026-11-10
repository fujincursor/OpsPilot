import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { agentService, chatService, knowledgeService, projectService, reviewService } from '../../services'
import type { ChatSessionSummary } from '../../services/chatService'
import type { Project } from '../../types'

interface Session {
  id: string
  title: string
  status: 'running' | 'pending' | 'complete' | 'error'
  time: string
  date: string
}

interface SidebarProps {
  currentProject?: string
  sessions?: Session[]
}

function formatSessionDate(value: string): { date: string; time: string } {
  const parsed = new Date(value)
  const today = new Date()
  const startToday = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const startDate = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate())
  const dayDiff = Math.round((startToday.getTime() - startDate.getTime()) / 86400000)
  const date = dayDiff === 0 ? '今天' : dayDiff === 1 ? '昨天' : parsed.toLocaleDateString('zh-CN')
  const time = parsed.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return { date, time }
}

function toSidebarSession(item: ChatSessionSummary): Session {
  const { date, time } = formatSessionDate(item.updated_at)
  return {
    id: item.id,
    title: item.title,
    status: item.status,
    time,
    date,
  }
}

export default function Sidebar({ currentProject }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [pendingReviewCount, setPendingReviewCount] = useState(0)
  const [projectId, setProjectId] = useState<string | null>(null)
  const [projectName, setProjectName] = useState(currentProject || '未选择项目')
  const [knowledgeReady, setKnowledgeReady] = useState<boolean | null>(null)
  const [enabledAgentCount, setEnabledAgentCount] = useState(0)
  const [sessions, setSessions] = useState<Session[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [projectOpen, setProjectOpen] = useState(false)
  const [sessionQuery, setSessionQuery] = useState('')

  useEffect(() => {
    loadPendingReviewCount()
    projectService.getProjects()
      .then(async (loadedProjects) => {
        setProjects(loadedProjects)
        const savedId = localStorage.getItem('opspilot.currentProjectId')
        const project = currentProject
          ? loadedProjects.find((item) => item.name === currentProject) || loadedProjects[0]
          : loadedProjects.find((item) => item.id === savedId) || loadedProjects[0]
        if (!project) {
          setProjectId(null)
          setProjectName('未选择项目')
          setKnowledgeReady(null)
          setEnabledAgentCount(0)
          return
        }
        setProjectId(project.id)
        setProjectName(project.name)
        localStorage.setItem('opspilot.currentProjectId', project.id)
        const [knowledgeBases, agents, readyStatus] = await Promise.all([
          knowledgeService.getKnowledgeBases(project.id).catch(() => []),
          agentService.getAgentConfigs(project.id).catch(() => []),
          knowledgeService.getReadyStatus(project.id).catch(() => null),
        ])
        setKnowledgeReady(readyStatus ? readyStatus.is_ready : knowledgeBases.some((item) => item.status === 'ready'))
        setEnabledAgentCount(agents.filter((agent) => agent.enabled).length)
      })
      .catch(() => {
        setProjectId(null)
        setProjectName(currentProject || '未选择项目')
        setKnowledgeReady(null)
        setEnabledAgentCount(0)
      })
  }, [currentProject])

  useEffect(() => {
    if (!projectId) {
      setSessions([])
      return
    }
    chatService.listSessions(projectId)
      .then((items) => setSessions(items.map(toSidebarSession)))
      .catch(() => setSessions([]))
  }, [projectId, location.pathname])

  const loadPendingReviewCount = async () => {
    try {
      const reviews = await reviewService.getPendingReviews()
      const count = reviews.filter((r) => r.status === 'pending').length
      setPendingReviewCount(count)
    } catch {
      setPendingReviewCount(0)
    }
  }

  const statusConfig = {
    running: { className: 'bg-blue-100 text-blue-600', text: '进行中' },
    pending: { className: 'bg-amber-100 text-amber-600', text: '待审批' },
    complete: { className: 'bg-green-100 text-green-600', text: '已完成' },
    error: { className: 'bg-red-100 text-red-600', text: '未完成' },
  }

  const visibleSessions = sessions.filter((session) =>
    session.title.toLowerCase().includes(sessionQuery.trim().toLowerCase())
  )
  const groupedSessions = visibleSessions.reduce((acc, session) => {
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
        <div className="relative">
        <div
          onClick={() => setProjectOpen((open) => !open)}
          className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-primary-light transition-colors"
        >
          <div className="flex items-center justify-between text-sm font-semibold text-gray-800">
            <span>🏢 {projectName}</span>
            <span className="text-gray-400">▼</span>
          </div>
          <div className="mt-2 space-y-1">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className={`w-1.5 h-1.5 rounded-full ${knowledgeReady ? 'bg-green-500' : 'bg-gray-300'}`}></span>
              知识库: {knowledgeReady === null ? '未知' : knowledgeReady ? '就绪' : '未就绪'}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className={`w-1.5 h-1.5 rounded-full ${enabledAgentCount > 0 ? 'bg-green-500' : 'bg-gray-300'}`}></span>
              Agent: {enabledAgentCount}
            </div>
          </div>
        </div>
        {projectOpen && (
          <div className="absolute z-10 mt-1 w-full max-h-48 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
            {projects.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  localStorage.setItem('opspilot.currentProjectId', item.id)
                  setProjectId(item.id)
                  setProjectName(item.name)
                  setProjectOpen(false)
                  knowledgeService.getReadyStatus(item.id).then((status) => setKnowledgeReady(status.is_ready)).catch(() => setKnowledgeReady(null))
                  agentService.getAgentConfigs(item.id).then((agents) => setEnabledAgentCount(agents.filter((agent) => agent.enabled).length)).catch(() => setEnabledAgentCount(0))
                  navigate(`/projects/${item.id}`)
                }}
                className="block w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
              >
                {item.name}
              </button>
            ))}
          </div>
        )}
        </div>
        <button
          onClick={() => navigate('/projects')}
          className="w-full mt-3 py-2 text-sm text-primary hover:text-primary-hover font-medium flex items-center justify-center gap-1.5 bg-primary-light hover:bg-primary/20 rounded-lg transition-colors"
        >
          📁 项目管理
        </button>
        <button
          onClick={() => navigate('/reviews')}
          className={`w-full mt-2 py-2 text-sm font-medium flex items-center justify-center gap-1.5 rounded-lg transition-colors ${
            location.pathname.startsWith('/reviews')
              ? 'bg-primary text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          ✅ Review 工作台
          {pendingReviewCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold bg-red-500 text-white rounded-full">
              {pendingReviewCount}
            </span>
          )}
        </button>
        <button
          onClick={() => navigate(projectId ? `/projects/${projectId}/dashboard` : '/projects')}
          className={`w-full mt-2 py-2 text-sm font-medium flex items-center justify-center gap-1.5 rounded-lg transition-colors ${
            location.pathname.includes('/dashboard')
              ? 'bg-primary text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          📊 运营看板
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-2">
        <input
          value={sessionQuery}
          onChange={(event) => setSessionQuery(event.target.value)}
          placeholder="搜索会话"
          className="mb-2 w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
        />
        {visibleSessions.length === 0 && (
          <div className="px-3 py-6 text-center text-xs text-gray-400">暂无会话</div>
        )}
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
                  <span>{session.time}</span>
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
