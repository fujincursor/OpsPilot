import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { NotificationBell } from '../Reviews'
import { authService } from '../../services/authService'
import api from '../../services/api'

interface HeaderProps {
  agentStatus?: 'ready' | 'busy' | 'offline'
  userName?: string
}

export default function Header({ agentStatus, userName }: HeaderProps) {
  const storedUser = authService.getUser()
  const [status, setStatus] = useState<'ready' | 'busy' | 'offline'>(agentStatus || 'offline')
  const displayName = userName || storedUser?.username || '用户'

  useEffect(() => {
    if (agentStatus) {
      setStatus(agentStatus)
      return
    }
    api.get<{ available: boolean }>('/deerflow/status')
      .then((response) => setStatus(response.data.available ? 'ready' : 'offline'))
      .catch(() => setStatus('offline'))
  }, [agentStatus])
  const statusConfig = {
    ready: { emoji: '🟢', text: 'Agent 就绪' },
    busy: { emoji: '🟡', text: 'Agent 执行中' },
    offline: { emoji: '🔴', text: 'Agent 离线' },
  }

  const statusInfo = statusConfig[status]

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 sticky top-0 z-50">
      <div className="flex items-center gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">🚀</span>
          <div className="flex flex-col leading-tight">
            <span className="text-base font-semibold text-gray-800">OpsPilot</span>
            <span className="text-xs text-gray-500">运维领航</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-light text-primary'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            工作台
          </NavLink>
          <NavLink
            to="/projects"
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-light text-primary'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            项目管理
          </NavLink>
          <NavLink
            to="/chat"
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-light text-primary'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            对话
          </NavLink>
          <NavLink
            to="/reviews"
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-light text-primary'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            Review
          </NavLink>
          <NavLink
            to="/monitor"
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-light text-primary'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            监控
          </NavLink>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {/* Notifications */}
        <NotificationBell />

        {/* Agent Status */}
        <span className="text-sm text-gray-600 flex items-center gap-1">
          {statusInfo.emoji} {statusInfo.text}
        </span>

        {/* User Avatar */}
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm font-medium">
          {displayName.charAt(0)}
        </div>
      </div>
    </header>
  )
}
