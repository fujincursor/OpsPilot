import api from './api'
import type {
  Requirement,
  CreateRequirementRequest,
  UpdateRequirementRequest,
  RequirementFilters,
  RequirementStatus,
  AnalysisResult,
} from '../types'

interface ListResponse<T> {
  items: T[]
}

export interface RequirementStatistics {
  total: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  by_priority: Record<string, number>
}

export const requirementService = {
  async createRequirement(projectId: string, data: CreateRequirementRequest): Promise<Requirement> {
    const response = await api.post<Requirement>(`/projects/${projectId}/requirements`, data)
    return response.data
  },

  async getStatistics(projectId: string): Promise<RequirementStatistics> {
    const response = await api.get<RequirementStatistics>(`/projects/${projectId}/requirements/statistics`)
    return response.data
  },

  async getRequirements(projectId: string, filters?: RequirementFilters): Promise<Requirement[]> {
    const response = await api.get<ListResponse<Requirement>>(`/projects/${projectId}/requirements`, {
      params: filters,
    })
    return response.data.items
  },

  async getRequirement(reqId: string): Promise<Requirement> {
    const response = await api.get<Requirement>(`/requirements/${reqId}`)
    return response.data
  },

  async updateRequirement(reqId: string, data: UpdateRequirementRequest): Promise<Requirement> {
    const response = await api.put<Requirement>(`/requirements/${reqId}`, data)
    return response.data
  },

  async updateStatus(reqId: string, status: RequirementStatus): Promise<Requirement> {
    const response = await api.patch<Requirement>(`/requirements/${reqId}/status`, { status })
    return response.data
  },

  async analyzeText(text: string): Promise<AnalysisResult> {
    const response = await api.post<AnalysisResult>('/requirements/analyze', { text })
    return response.data
  },

  async assignRequirement(reqId: string, assignee: string): Promise<Requirement> {
    const response = await api.patch<Requirement>(`/requirements/${reqId}/assign`, { assignee })
    return response.data
  },

  async deleteRequirement(reqId: string): Promise<void> {
    await api.delete(`/requirements/${reqId}`)
  },
}

export default requirementService
