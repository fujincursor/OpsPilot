import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChatWindow } from '../components/Chat'
import { projectService } from '../services'

export default function Chat() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [projectName, setProjectName] = useState('未选择项目')
  const [projectId, setProjectId] = useState<string>()

  useEffect(() => {
    projectService.getProjects()
      .then((projects) => {
        const savedId = localStorage.getItem('opspilot.currentProjectId')
        const project = projects.find((item) => item.id === savedId) || projects[0]
        if (!project) return
        setProjectId(project.id)
        setProjectName(project.name)
        localStorage.setItem('opspilot.currentProjectId', project.id)
      })
      .catch(() => setProjectName('未选择项目'))
  }, [])

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
