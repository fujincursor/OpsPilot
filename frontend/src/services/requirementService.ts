import api from './api'
import type {
  Requirement,
  CreateRequirementRequest,
  UpdateRequirementRequest,
  RequirementFilters,
  RequirementStatus,
  AnalysisResult,
  ApiResponse,
  StatusHistoryItem,
} from '../types'

export const requirementService = {
  async createRequirement(
    projectId: string,
    data: CreateRequirementRequest
  ): Promise<Requirement> {
    const response = await api.post<ApiResponse<Requirement>>(
      `/projects/${projectId}/requirements`,
      data
    )
    return response.data.data
  },

  async getRequirements(
    projectId: string,
    filters?: RequirementFilters
  ): Promise<Requirement[]> {
    const params = new URLSearchParams()
    if (filters?.type) params.append('type', filters.type)
    if (filters?.status) params.append('status', filters.status)
    if (filters?.priority) params.append('priority', filters.priority)
    if (filters?.assignee) params.append('assignee', filters.assignee)

    const queryString = params.toString()
    const url = `/projects/${projectId}/requirements${queryString ? `?${queryString}` : ''}`
    
    const response = await api.get<ApiResponse<Requirement[]>>(url)
    return response.data.data
  },

  async getRequirement(reqId: string): Promise<Requirement> {
    const response = await api.get<ApiResponse<Requirement>>(
      `/requirements/${reqId}`
    )
    return response.data.data
  },

  async updateRequirement(
    reqId: string,
    data: UpdateRequirementRequest
  ): Promise<Requirement> {
    const response = await api.patch<ApiResponse<Requirement>>(
      `/requirements/${reqId}`,
      data
    )
    return response.data.data
  },

  async updateStatus(
    reqId: string,
    status: RequirementStatus,
    comment?: string
  ): Promise<Requirement> {
    const response = await api.patch<ApiResponse<Requirement>>(
      `/requirements/${reqId}/status`,
      { status, comment }
    )
    return response.data.data
  },

  async analyzeText(text: string): Promise<AnalysisResult> {
    const response = await api.post<ApiResponse<AnalysisResult>>(
      '/requirements/analyze',
      { text }
    )
    return response.data.data
  },

  async getStatusHistory(reqId: string): Promise<StatusHistoryItem[]> {
    const response = await api.get<ApiResponse<StatusHistoryItem[]>>(
      `/requirements/${reqId}/history`
    )
    return response.data.data
  },

  async assignRequirement(reqId: string, assignee: string): Promise<Requirement> {
    const response = await api.patch<ApiResponse<Requirement>>(
      `/requirements/${reqId}`,
      { assignee }
    )
    return response.data.data
  },

  async deleteRequirement(reqId: string): Promise<void> {
    await api.delete(`/requirements/${reqId}`)
  },
}

export default requirementService
