import api from './api'
import type { AgentConfig, UpdateAgentConfigRequest, ApiResponse } from '../types'

export const agentService = {
  async getAgentConfigs(projectId: string): Promise<AgentConfig[]> {
    const response = await api.get<ApiResponse<AgentConfig[]>>(
      `/projects/${projectId}/agents`
    )
    return response.data.data
  },

  async getAgentConfig(projectId: string, agentId: string): Promise<AgentConfig> {
    const response = await api.get<ApiResponse<AgentConfig>>(
      `/projects/${projectId}/agents/${agentId}`
    )
    return response.data.data
  },

  async updateAgentConfig(
    projectId: string,
    agentId: string,
    data: UpdateAgentConfigRequest
  ): Promise<AgentConfig> {
    const response = await api.put<ApiResponse<AgentConfig>>(
      `/projects/${projectId}/agents/${agentId}`,
      data
    )
    return response.data.data
  },

  async toggleAgent(projectId: string, agentId: string, enabled: boolean): Promise<AgentConfig> {
    const response = await api.patch<ApiResponse<AgentConfig>>(
      `/projects/${projectId}/agents/${agentId}/toggle`,
      { enabled }
    )
    return response.data.data
  },

  async resetAgentConfig(projectId: string, agentId: string): Promise<AgentConfig> {
    const response = await api.post<ApiResponse<AgentConfig>>(
      `/projects/${projectId}/agents/${agentId}/reset`
    )
    return response.data.data
  },
}

export default agentService
