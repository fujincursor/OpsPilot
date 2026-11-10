import api from './api'
import type {
  KnowledgeBase,
  Document,
  CreateKnowledgeBaseRequest,
  ApiResponse,
  SearchResult,
  KnowledgeStatusSummary,
} from '../types'

export const knowledgeService = {
  async getKnowledgeBases(projectId: string): Promise<KnowledgeBase[]> {
    const response = await api.get<ApiResponse<KnowledgeBase[]>>(
      `/projects/${projectId}/knowledge-bases`
    )
    return response.data.data
  },

  async createKnowledgeBase(
    projectId: string,
    data: CreateKnowledgeBaseRequest
  ): Promise<KnowledgeBase> {
    const response = await api.post<ApiResponse<KnowledgeBase>>(
      `/projects/${projectId}/knowledge-bases`,
      data
    )
    return response.data.data
  },

  async getKnowledgeBase(kbId: string): Promise<KnowledgeBase> {
    const response = await api.get<ApiResponse<KnowledgeBase>>(
      `/knowledge-bases/${kbId}`
    )
    return response.data.data
  },

  async deleteKnowledgeBase(kbId: string): Promise<void> {
    await api.delete(`/knowledge-bases/${kbId}`)
  },

  async getDocuments(kbId: string): Promise<Document[]> {
    const response = await api.get<ApiResponse<Document[]>>(
      `/knowledge-bases/${kbId}/documents`
    )
    return response.data.data
  },

  async uploadDocument(
    kbId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<ApiResponse<Document>>(
      `/knowledge-bases/${kbId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
            onProgress(progress)
          }
        },
      }
    )
    return response.data.data
  },

  async deleteDocument(docId: string): Promise<void> {
    await api.delete(`/documents/${docId}`)
  },

  async searchKnowledge(
    projectId: string,
    query: string,
    limit = 10
  ): Promise<SearchResult[]> {
    const response = await api.post<ApiResponse<SearchResult[]>>(
      `/projects/${projectId}/knowledge/search`,
      { query, limit }
    )
    return response.data.data
  },

  async getKnowledgeStatus(projectId: string): Promise<KnowledgeStatusSummary> {
    const response = await api.get<ApiResponse<KnowledgeStatusSummary>>(
      `/projects/${projectId}/knowledge/status`
    )
    return response.data.data
  },
}

export default knowledgeService
