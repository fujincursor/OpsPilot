import { useParams } from 'react-router-dom'
import { ChatWindow, Message } from '../components/Chat'

const mockMessages: Message[] = [
  {
    id: '1',
    type: 'user',
    content: '用户登录接口报 500 错误，日志显示数据库连接超时，请帮忙排查一下',
    sender: '张三',
    timestamp: '10:30',
  },
  {
    id: '2',
    type: 'agent',
    content: '我已完成问题分析，以下是结果：',
    sender: 'Lead Agent',
    timestamp: '10:32',
    agentType: 'lead',
    status: 'complete',
    knowledgeResults: [
      {
        title: '项目架构说明.md',
        relevance: 92,
        snippet: '"...数据库连接池配置位于 config/db-pool.yaml，默认最大连接数为 10..."',
      },
      {
        title: '数据库配置指南.md',
        relevance: 87,
        snippet: '"...高并发场景建议将 maxConnections 设置为 50 以上..."',
      },
    ],
    classifyResult: {
      type: 'bug',
      priority: 'high',
      ticketId: 'BUG-2024-001',
    },
  },
  {
    id: '3',
    type: 'agent',
    content: '正在分析问题根因并生成修复方案...',
    sender: 'Bug Fix Agent',
    timestamp: '10:33',
    agentType: 'bugfix',
    status: 'analyzing',
    agentSteps: [
      { id: 1, name: '代码定位 - 找到相关代码文件', status: 'done' },
      { id: 2, name: '问题分析 - 识别根本原因', status: 'done' },
      { id: 3, name: '方案生成 - 生成修复方案中...', status: 'running' },
      { id: 4, name: '方案审批 - 等待人工审批', status: 'pending' },
    ],
    progress: 60,
  },
]

export default function Chat() {
  const { sessionId } = useParams<{ sessionId: string }>()

  const hasExistingSession = !!sessionId

  return (
    <div className="h-[calc(100vh-56px)] bg-gray-50">
      <ChatWindow
        sessionId={sessionId}
        initialMessages={hasExistingSession ? mockMessages : []}
        projectName="项目 Alpha"
      />
    </div>
  )
}
