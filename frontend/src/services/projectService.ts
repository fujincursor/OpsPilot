import api from './api'
import axios from 'axios'
import type { Project, CreateProjectRequest, SandboxTestResult, UpdateProjectRequest } from '../types'

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

  async testSandbox(id: string): Promise<SandboxTestResult> {
    const response = await api.post<SandboxTestResult>(`/projects/${id}/sandbox/test`)
    return response.data
  },

  async archiveProject(id: string): Promise<Project> {
    const response = await api.put<Project>(`/projects/${id}`, { status: 'archived' })
    return response.data
  },

  async importGit(id: string, repoUrl: string, branch = ''): Promise<Project> {
    const response = await api.post<Project>(`/projects/${id}/code/git`, {
      repo_url: repoUrl,
      branch,
    }, { timeout: 130000 })
    return response.data
  },

  async uploadSource(id: string, file: File): Promise<Project> {
    const form = new FormData()
    form.append('file', file)
    const response = await api.post<Project>(`/projects/${id}/code/upload`, form, {
      timeout: 130000,
      transformRequest: [(data, headers) => {
        if (headers && typeof (headers as { delete?: (name: string) => void }).delete === 'function') {
          (headers as { delete: (name: string) => void }).delete('Content-Type')
        }
        return data
      }],
    })
    return response.data
  },
}

export function projectErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
  }
  return fallback
}

export default projectService
