import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import Knowledge from './pages/Knowledge'
import KnowledgeDetail from './pages/KnowledgeDetail'
import Requirements from './pages/Requirements'
import RequirementDetail from './pages/RequirementDetail'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="chat" element={<Chat />} />
        <Route path="chat/:sessionId" element={<Chat />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="projects/:id/knowledge" element={<Knowledge />} />
        <Route path="projects/:id/requirements" element={<Requirements />} />
        <Route path="knowledge/:kbId" element={<KnowledgeDetail />} />
        <Route path="requirements/:reqId" element={<RequirementDetail />} />
      </Route>
    </Routes>
  )
}

export default App
