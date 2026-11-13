import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChatWindow } from '../components/Chat'
import { chatService, projectService } from '../services'

export default function Chat() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [projectName, setProjectName] = useState('未选择项目')
  const [projectId, setProjectId] = useState<string>()

  useEffect(() => {
    let active = true
    const applySaved = (projects: Awaited<ReturnType<typeof projectService.getProjects>>) => {
      const savedId = localStorage.getItem('opspilot.currentProjectId')
      const project = projects.find((item) => item.id === savedId) || projects[0]
      if (!project || !active) return
      setProjectId(project.id)
      setProjectName(project.name)
      localStorage.setItem('opspilot.currentProjectId', project.id)
    }
    projectService.getProjects()
      .then(async (projects) => {
        if (!active) return
        if (!sessionId) {
          applySaved(projects)
          return
        }
        try {
          const session = await chatService.getSession(sessionId)
          const project = projects.find((item) => item.id === session.project_id)
          if (!active) return
          if (project) {
            setProjectId(project.id)
            setProjectName(project.name)
            return
          }
        } catch {
          /* 会话读取失败时继续使用当前项目 */
        }
        applySaved(projects)
      })
      .catch(() => {
        if (active) setProjectName('未选择项目')
      })
    return () => {
      active = false
    }
  }, [sessionId])

  return (
    <div className="h-[calc(100vh-56px)] bg-gray-50">
      <ChatWindow
        sessionId={sessionId}
        projectId={projectId}
        projectName={projectName}
        onSessionReady={(id) => {
          if (id !== sessionId) navigate(`/chat/${id}`, { replace: true })
        }}
      />
    </div>
  )
}
