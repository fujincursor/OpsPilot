import api from './api'
import type {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  ApiResponse,
  PaginatedResponse,
} from '../types'

export const projectService = {
  async getProjects(page = 1, pageSize = 10): Promise<PaginatedResponse<Project>> {
    const response = await api.get<PaginatedResponse<Project>>('/projects', {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  async getProject(id: string): Promise<Project> {
    const response = await api.get<ApiResponse<Project>>(`/projects/${id}`)
    return response.data.data
  },

  async createProject(data: CreateProjectRequest): Promise<Project> {
    const response = await api.post<ApiResponse<Project>>('/projects', data)
    return response.data.data
  },

  async updateProject(id: string, data: UpdateProjectRequest): Promise<Project> {
    const response = await api.put<ApiResponse<Project>>(`/projects/${id}`, data)
    return response.data.data
  },

  async deleteProject(id: string): Promise<void> {
    await api.delete(`/projects/${id}`)
  },

  async archiveProject(id: string): Promise<Project> {
    const response = await api.post<ApiResponse<Project>>(`/projects/${id}/archive`)
    return response.data.data
  },
}

export default projectService
