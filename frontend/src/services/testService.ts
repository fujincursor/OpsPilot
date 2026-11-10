import api from './api'
import type {
  TestTask,
  TestCase,
  TestResult,
  TestReport,
  TestTaskSummary,
  ApiResponse,
} from '../types'

export const testService = {
  async createTestTask(codegenTaskId: string): Promise<TestTask> {
    const response = await api.post<ApiResponse<TestTask>>(
      `/codegen/${codegenTaskId}/tests`
    )
    return response.data.data
  },

  async getTestTask(taskId: string): Promise<TestTask> {
    const response = await api.get<ApiResponse<TestTask>>(
      `/tests/${taskId}`
    )
    return response.data.data
  },

  async getTestCases(taskId: string): Promise<TestCase[]> {
    const response = await api.get<ApiResponse<TestCase[]>>(
      `/tests/${taskId}/cases`
    )
    return response.data.data
  },

  async getTestResults(taskId: string): Promise<TestResult[]> {
    const response = await api.get<ApiResponse<TestResult[]>>(
      `/tests/${taskId}/results`
    )
    return response.data.data
  },

  async getTestReport(taskId: string): Promise<TestReport> {
    const response = await api.get<ApiResponse<TestReport>>(
      `/tests/${taskId}/report`
    )
    return response.data.data
  },

  async rerunTests(taskId: string): Promise<TestTask> {
    const response = await api.post<ApiResponse<TestTask>>(
      `/tests/${taskId}/rerun`
    )
    return response.data.data
  },

  async triggerCI(taskId: string): Promise<{ ci_url: string }> {
    const response = await api.post<ApiResponse<{ ci_url: string }>>(
      `/tests/${taskId}/trigger-ci`
    )
    return response.data.data
  },

  async submitForReview(taskId: string): Promise<TestTask> {
    const response = await api.post<ApiResponse<TestTask>>(
      `/tests/${taskId}/submit-review`
    )
    return response.data.data
  },

  async getTasksByCodegen(codegenTaskId: string): Promise<TestTaskSummary[]> {
    const response = await api.get<ApiResponse<TestTaskSummary[]>>(
      `/codegen/${codegenTaskId}/tests`
    )
    return response.data.data
  },
}

export default testService
