import api from './api'
import type {
  Solution,
  BugFixSolution,
  FeatureDesignSolution,
  SolutionStatus,
  ApiResponse,
} from '../types'

export const solutionService = {
  async generateSolution(reqId: string): Promise<Solution> {
    const response = await api.post<ApiResponse<Solution>>(
      `/requirements/${reqId}/solutions/generate`
    )
    return response.data.data
  },

  async getSolutions(reqId: string): Promise<Solution[]> {
    const response = await api.get<ApiResponse<Solution[]>>(
      `/requirements/${reqId}/solutions`
    )
    return response.data.data
  },

  async getSolution(solutionId: string): Promise<BugFixSolution | FeatureDesignSolution> {
    const response = await api.get<ApiResponse<BugFixSolution | FeatureDesignSolution>>(
      `/solutions/${solutionId}`
    )
    return response.data.data
  },

  async updateSolutionStatus(
    solutionId: string,
    status: SolutionStatus,
    comment?: string
  ): Promise<Solution> {
    const response = await api.patch<ApiResponse<Solution>>(
      `/solutions/${solutionId}/status`,
      { status, comment }
    )
    return response.data.data
  },

  async regenerateSolution(solutionId: string): Promise<Solution> {
    const response = await api.post<ApiResponse<Solution>>(
      `/solutions/${solutionId}/regenerate`
    )
    return response.data.data
  },
}

export default solutionService
