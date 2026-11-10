import api from './api'
import type {
  KnowledgeBase,
  Document,
  CreateKnowledgeBaseRequest,
  SearchResult,
} from '../types'

interface ListResponse<T> {
  items: T[]
  total: number
}

interface SearchResponse {
  results: Array<{
    document_id: string
    title: string
    content_snippet: string
    score: number
    knowledge_base_id: string
  }>
}

export const knowledgeService = {
  async getKnowledgeBases(projectId: string): Promise<KnowledgeBase[]> {
    const response = await api.get<ListResponse<KnowledgeBase>>(`/projects/${projectId}/knowledge`)
    return response.data.items
  },

  async createKnowledgeBase(
    projectId: string,
    data: CreateKnowledgeBaseRequest
  ): Promise<KnowledgeBase> {
    const response = await api.post<KnowledgeBase>(`/projects/${projectId}/knowledge`, data)
    return response.data
  },

  async getKnowledgeBase(kbId: string): Promise<KnowledgeBase> {
    const response = await api.get<KnowledgeBase>(`/knowledge/${kbId}`)
    return response.data
  },

  async getReadyStatus(projectId: string): Promise<{ is_ready: boolean; message: string }> {
    const response = await api.get<{ is_ready: boolean; message: string }>(
      `/projects/${projectId}/knowledge/status`
    )
    return response.data
  },

  async updateKnowledgeBase(
    kbId: string,
    data: Partial<Pick<KnowledgeBase, 'name' | 'description' | 'type' | 'index_paths' | 'index_trigger' | 'update_policy'>>
  ): Promise<KnowledgeBase> {
    const response = await api.put<KnowledgeBase>(`/knowledge/${kbId}`, data)
    return response.data
  },

  async startIndex(kbId: string): Promise<KnowledgeBase> {
    const response = await api.post<KnowledgeBase>(`/knowledge/${kbId}/index`)
    return response.data
  },

  async deleteKnowledgeBase(kbId: string): Promise<void> {
    await api.delete(`/knowledge/${kbId}`)
  },

  async getDocuments(kbId: string): Promise<Document[]> {
    const response = await api.get<ListResponse<Document>>(`/knowledge/${kbId}/documents`)
    return response.data.items
  },

  async uploadDocument(kbId: string, file: File): Promise<Document> {
    const content = await file.text()
    const response = await api.post<Document>(`/knowledge/${kbId}/documents`, {
      title: file.name,
      content,
      file_path: file.name,
      file_type: file.name.split('.').pop() || 'txt',
    })
    return response.data
  },

  async deleteDocument(docId: string): Promise<void> {
    await api.delete(`/documents/${docId}`)
  },

  async searchKnowledge(projectId: string, query: string, limit = 10): Promise<SearchResult[]> {
    const response = await api.post<SearchResponse>(`/projects/${projectId}/knowledge/search`, {
      query,
      top_k: limit,
    })
    return response.data.results.map((item) => ({
      document_id: item.document_id,
      title: item.title,
      content: item.content_snippet,
      score: item.score,
      knowledge_base_name: item.knowledge_base_id,
    }))
  },
}

export default knowledgeService
