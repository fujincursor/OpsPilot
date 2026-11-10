export interface Project {
  id: string
  name: string
  description: string
  repo_url: string
  status: 'active' | 'inactive' | 'archived'
  created_at: string
  updated_at: string
}

export interface AgentConfig {
  id: string
  project_id: string
  agent_type: 'lead' | 'bugfix' | 'feature' | 'doc' | 'review'
  name: string
  description: string
  model_name: string
  temperature: number
  max_tokens: number
  skills: string[]
  enabled: boolean
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'developer' | 'viewer'
}

export interface CreateProjectRequest {
  name: string
  description: string
  repo_url: string
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  repo_url?: string
  status?: Project['status']
}

export interface UpdateAgentConfigRequest {
  model_name?: string
  temperature?: number
  max_tokens?: number
  skills?: string[]
  enabled?: boolean
}

export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}
