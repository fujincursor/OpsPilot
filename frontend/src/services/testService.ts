import api from './api'
import type { TestTask, TestCase, TestResult, TestReport, TestTaskSummary, CIPipeline } from '../types'

interface ListResponse<T> {
  items: T[]
}

export const testService = {
  async createTestTask(codegenTaskId: string): Promise<TestTask> {
    const response = await api.post<TestTask>(`/codegen/${codegenTaskId}/tests`)
    return response.data
  },

  async getTestTask(taskId: string): Promise<TestTask> {
    const response = await api.get<TestTask>(`/tests/${taskId}`)
    return response.data
  },

  async getTestCases(taskId: string): Promise<TestCase[]> {
    const response = await api.get<TestCase[]>(`/tests/${taskId}/cases`)
    return response.data
  },

  async getTestResults(taskId: string): Promise<TestResult[]> {
    const response = await api.get<TestResult[]>(`/tests/${taskId}/results`)
    return response.data
  },

  async getTestReport(taskId: string): Promise<TestReport> {
    const response = await api.get<TestReport>(`/tests/${taskId}/report`)
    return response.data
  },

  async rerunTests(taskId: string): Promise<TestTask> {
    const response = await api.post<TestTask>(`/tests/${taskId}/rerun`)
    return response.data
  },

  async triggerCI(taskId: string): Promise<CIPipeline> {
    const response = await api.post<CIPipeline>(`/tests/${taskId}/trigger-ci`, null, {
      timeout: 120000,
    })
    return response.data
  },

  async getCI(taskId: string): Promise<CIPipeline | null> {
    try {
      const response = await api.get<CIPipeline>(`/tests/${taskId}/ci-status`)
      return response.data
    } catch {
      return null
    }
  },

  async submitForReview(taskId: string): Promise<TestTask> {
    const response = await api.post<TestTask>(`/tests/${taskId}/submit-review`, {
      approve_with_failures: true,
    })
    return response.data
  },

  async getTasksByCodegen(codegenTaskId: string): Promise<TestTaskSummary[]> {
    const response = await api.get<ListResponse<TestTaskSummary>>('/tests', {
      params: { codegen_task_id: codegenTaskId },
    })
    return response.data.items || []
  },
}

export default testService
