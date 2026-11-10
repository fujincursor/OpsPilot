import api from './api'
import type { Message } from '../components/Chat/MessageList'

export interface ChatSessionSummary {
  id: string
  project_id: string
  title: string
  message_count: number
  status: 'complete' | 'error' | 'pending' | 'running'
  created_at: string
  updated_at: string
}

interface StoredKnowledgeHit {
  title: string
  snippet: string
  score: number
}

interface StoredClassification {
  type: 'bug' | 'feature' | 'question'
  priority: 'high' | 'medium' | 'low'
  title?: string
  ticket_id?: string | null
}

interface StoredReviewCard {
  review_id: string
  item_type: string
  title: string
  status: string
  summary: string
  root_cause?: string
  files?: string[]
  due_at?: string | null
}

interface StoredMessage {
  id: string
  role: 'user' | 'agent'
  content: string
  sender: string
  status?: 'analyzing' | 'complete' | 'error' | null
  knowledge_results?: StoredKnowledgeHit[]
  classification?: StoredClassification | null
  review?: StoredReviewCard | null
  knowledge_blocked?: boolean
  created_at: string
}

export interface ChatSessionDetail {
  id: string
  project_id: string
  title: string
  messages: StoredMessage[]
  created_at: string
  updated_at: string
}

function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

export function toChatMessages(messages: StoredMessage[], projectId?: string): Message[] {
  return messages.map((message) => ({
    id: message.id,
    type: message.role === 'agent' ? 'agent' : 'user',
    content: message.content,
    sender: message.sender,
    timestamp: formatTime(message.created_at),
    agentType: message.role === 'agent' ? 'lead' : undefined,
    status: message.role === 'agent' ? message.status || 'complete' : undefined,
    knowledgeResults: (message.knowledge_results || []).map((item) => ({
      title: item.title,
      snippet: item.snippet,
      relevance: Math.round(item.score * 100),
    })),
    classifyResult: message.classification
      ? {
          type: message.classification.type,
          priority: message.classification.priority,
          ticketId: message.classification.ticket_id || '',
        }
      : undefined,
    agentSteps: message.classification
      ? [
          { id: 1, name: '知识检索', status: 'done' as const },
          { id: 2, name: '需求分类', status: 'done' as const },
          {
            id: 3,
            name: message.classification.type === 'question' ? '直接回答' : '方案与审批',
            status: message.classification.type === 'question' ? 'done' as const : 'running' as const,
          },
        ]
      : undefined,
    progress: message.classification ? (message.classification.type === 'question' ? 100 : 66) : undefined,
    review: message.review
      ? {
          reviewId: message.review.review_id,
          itemType: message.review.item_type,
          title: message.review.title,
          status: message.review.status,
          summary: message.review.summary,
          rootCause: message.review.root_cause || '',
          files: message.review.files || [],
          dueAt: message.review.due_at || '',
        }
      : undefined,
    knowledgeProjectId: message.knowledge_blocked ? projectId : undefined,
  }))
}

export const chatService = {
  async listSessions(projectId: string): Promise<ChatSessionSummary[]> {
    const response = await api.get<{ items: ChatSessionSummary[] }>(`/projects/${projectId}/chats`)
    return response.data.items
  },

  async getSession(sessionId: string): Promise<ChatSessionDetail> {
    const response = await api.get<ChatSessionDetail>(`/chats/${sessionId}`)
    return response.data
  },
}

export default chatService
