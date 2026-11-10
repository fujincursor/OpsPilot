import api from './api'
import type { AgentConfig, UpdateAgentConfigRequest } from '../types'

interface ListResponse<T> {
  items: T[]
  total: number
}

export const agentService = {
  async getAgentConfigs(projectId: string): Promise<AgentConfig[]> {
    const response = await api.get<ListResponse<AgentConfig>>(`/projects/${projectId}/agents`)
    return response.data.items
  },

  async getAgentConfig(agentId: string): Promise<AgentConfig> {
    const response = await api.get<AgentConfig>(`/agents/${agentId}`)
    return response.data
  },

  async updateAgentConfig(
    _projectId: string,
    agentId: string,
    data: UpdateAgentConfigRequest
  ): Promise<AgentConfig> {
    const response = await api.put<AgentConfig>(`/agents/${agentId}`, data)
    return response.data
  },

  async toggleAgent(projectId: string, agentId: string, enabled: boolean): Promise<AgentConfig> {
    return this.updateAgentConfig(projectId, agentId, { enabled })
  },
}

export default agentService
