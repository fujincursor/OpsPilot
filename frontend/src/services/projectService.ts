import api from './api'
import type { Project, CreateProjectRequest, UpdateProjectRequest } from '../types'

interface ListResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const projectService = {
  async getProjects(page = 1, pageSize = 100): Promise<Project[]> {
    const response = await api.get<ListResponse<Project>>('/projects', {
      params: { page, page_size: pageSize },
    })
    return response.data.items
  },

  async getProject(id: string): Promise<Project> {
    const response = await api.get<Project>(`/projects/${id}`)
    return response.data
  },

  async createProject(data: CreateProjectRequest): Promise<Project> {
    const response = await api.post<Project>('/projects', data)
    return response.data
  },

  async updateProject(id: string, data: UpdateProjectRequest): Promise<Project> {
    const response = await api.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  async deleteProject(id: string): Promise<void> {
    await api.delete(`/projects/${id}`)
  },

  async getSkillContent(key: string): Promise<{ key: string; name: string; description: string; content: string }> {
    const response = await api.get<{ key: string; name: string; description: string; content: string }>(`/skills/${encodeURIComponent(key)}`)
    return response.data
  },

  async testSandbox(id: string): Promise<{ ok: boolean; message: string }> {
    const response = await api.post<{ ok: boolean; message: string }>(`/projects/${id}/sandbox/test`)
    return response.data
  },

  async archiveProject(id: string): Promise<Project> {
    const response = await api.put<Project>(`/projects/${id}`, { status: 'archived' })
    return response.data
  },
}

export default projectService
