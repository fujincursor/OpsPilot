import api from './api'
import type {
  CodeGenTask,
  CodeFile,
  DiffLine,
  LintResult,
  ApiResponse,
  CodeGenTaskSummary,
} from '../types'

export const codegenService = {
  async createCodeGenTask(solutionId: string): Promise<CodeGenTask> {
    const response = await api.post<ApiResponse<CodeGenTask>>(
      `/solutions/${solutionId}/codegen`
    )
    return response.data.data
  },

  async getTaskStatus(taskId: string): Promise<CodeGenTask> {
    const response = await api.get<ApiResponse<CodeGenTask>>(
      `/codegen/${taskId}`
    )
    return response.data.data
  },

  async getGeneratedFiles(taskId: string): Promise<CodeFile[]> {
    const response = await api.get<ApiResponse<CodeFile[]>>(
      `/codegen/${taskId}/files`
    )
    return response.data.data
  },

  async getCodeDiff(taskId: string): Promise<DiffLine[]> {
    const response = await api.get<ApiResponse<DiffLine[]>>(
      `/codegen/${taskId}/diff`
    )
    return response.data.data
  },

  async getLintResult(taskId: string): Promise<LintResult> {
    const response = await api.get<ApiResponse<LintResult>>(
      `/codegen/${taskId}/lint`
    )
    return response.data.data
  },

  async regenerate(taskId: string): Promise<CodeGenTask> {
    const response = await api.post<ApiResponse<CodeGenTask>>(
      `/codegen/${taskId}/regenerate`
    )
    return response.data.data
  },

  async submitForReview(taskId: string): Promise<CodeGenTask> {
    const response = await api.post<ApiResponse<CodeGenTask>>(
      `/codegen/${taskId}/submit-review`
    )
    return response.data.data
  },

  async getTasksBySolution(solutionId: string): Promise<CodeGenTaskSummary[]> {
    const response = await api.get<ApiResponse<CodeGenTaskSummary[]>>(
      `/solutions/${solutionId}/codegen/tasks`
    )
    return response.data.data
  },
}

export default codegenService
