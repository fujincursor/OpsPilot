import api from './api'
import type { CodeGenTask, CodeFile, LintResult, CodeGenTaskSummary } from '../types'

interface ListResponse<T> {
  items: T[]
}

export const codegenService = {
  async createCodeGenTask(solutionId: string): Promise<CodeGenTask> {
    const response = await api.post<CodeGenTask>(`/solutions/${solutionId}/codegen`)
    return response.data
  },

  async getTaskStatus(taskId: string): Promise<CodeGenTask> {
    const response = await api.get<CodeGenTask>(`/codegen/${taskId}`)
    return response.data
  },

  async getGeneratedFiles(taskId: string): Promise<CodeFile[]> {
    const response = await api.get<CodeFile[]>(`/codegen/${taskId}/files`)
    return response.data
  },

  async getLintResult(taskId: string): Promise<LintResult> {
    const response = await api.get<LintResult>(`/codegen/${taskId}/lint`)
    return response.data
  },

  async regenerate(taskId: string): Promise<CodeGenTask> {
    const response = await api.post<CodeGenTask>(`/codegen/${taskId}/regenerate`)
    return response.data
  },

  async submitForReview(taskId: string): Promise<CodeGenTask> {
    const response = await api.post<CodeGenTask>(`/codegen/${taskId}/submit-review`)
    return response.data
  },

  async applyToProject(taskId: string): Promise<CodeGenTask> {
    const response = await api.post<CodeGenTask>(`/codegen/${taskId}/apply`)
    return response.data
  },

  async getTasksBySolution(solutionId: string): Promise<CodeGenTaskSummary[]> {
    const response = await api.get<ListResponse<CodeGenTaskSummary>>(
      `/solutions/${solutionId}/codegen/tasks`
    )
    return response.data.items
  },
}

export default codegenService
