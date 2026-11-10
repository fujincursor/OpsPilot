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

export type KnowledgeStatus = 'pending' | 'indexing' | 'ready' | 'error'
export type KnowledgeType = 'doc' | 'code' | 'faq'

export interface KnowledgeBase {
  id: string
  project_id: string
  name: string
  description: string
  type: KnowledgeType
  status: KnowledgeStatus
  document_count: number
  created_at: string
}

export interface Document {
  id: string
  knowledge_base_id: string
  title: string
  content: string
  file_path: string
  file_type: string
  embedding_status: KnowledgeStatus
  created_at: string
}

export interface CreateKnowledgeBaseRequest {
  name: string
  description: string
  type: KnowledgeType
}

export interface SearchResult {
  document_id: string
  title: string
  content: string
  score: number
  knowledge_base_name: string
}

export interface KnowledgeStatusSummary {
  total: number
  pending: number
  indexing: number
  ready: number
  error: number
}

export type RequirementType = 'bug' | 'feature' | 'question'
export type RequirementStatus = 'pending' | 'analyzing' | 'designing' | 'reviewing' | 'coding' | 'testing' | 'completed' | 'closed'
export type RequirementPriority = 'low' | 'medium' | 'high' | 'critical'

export interface AnalysisResult {
  type: RequirementType
  priority: RequirementPriority
  keywords: string[]
  confidence: number
}

export interface Requirement {
  id: string
  project_id: string
  title: string
  description: string
  source: string
  type: RequirementType
  priority: RequirementPriority
  status: RequirementStatus
  assignee?: string
  created_by: string
  analysis_result?: AnalysisResult
  created_at: string
  updated_at?: string
}

export interface CreateRequirementRequest {
  title: string
  description: string
  source?: string
  type?: RequirementType
  priority?: RequirementPriority
}

export interface UpdateRequirementRequest {
  title?: string
  description?: string
  type?: RequirementType
  priority?: RequirementPriority
  assignee?: string
}

export interface RequirementFilters {
  type?: RequirementType
  status?: RequirementStatus
  priority?: RequirementPriority
  assignee?: string
}

export interface StatusHistoryItem {
  status: RequirementStatus
  changed_at: string
  changed_by: string
  comment?: string
}
