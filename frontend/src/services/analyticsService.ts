import api from './api'
import type {
  DashboardStats,
  TrendData,
  AgentPerformance,
  QualityMetrics,
  EfficiencyMetrics,
  FunnelData,
  DateRange,
  ExportFormat,
  ApiResponse,
} from '../types'

const mockDashboardStats: DashboardStats = {
  total_requirements: 156,
  completed: 89,
  in_progress: 42,
  pending_review: 25,
  avg_completion_time: 4.2,
}

const mockTrendData: TrendData[] = [
  { date: '2024-01-01', count: 12, type: 'created' },
  { date: '2024-01-02', count: 8, type: 'created' },
  { date: '2024-01-03', count: 15, type: 'created' },
  { date: '2024-01-04', count: 10, type: 'created' },
  { date: '2024-01-05', count: 18, type: 'created' },
  { date: '2024-01-06', count: 14, type: 'created' },
  { date: '2024-01-07', count: 20, type: 'created' },
  { date: '2024-01-01', count: 8, type: 'completed' },
  { date: '2024-01-02', count: 10, type: 'completed' },
  { date: '2024-01-03', count: 12, type: 'completed' },
  { date: '2024-01-04', count: 9, type: 'completed' },
  { date: '2024-01-05', count: 15, type: 'completed' },
  { date: '2024-01-06', count: 11, type: 'completed' },
  { date: '2024-01-07', count: 16, type: 'completed' },
]

const mockAgentPerformance: AgentPerformance[] = [
  { agent_type: 'lead', tasks_completed: 156, success_rate: 98.5, avg_time: 1.2 },
  { agent_type: 'bugfix', tasks_completed: 89, success_rate: 95.2, avg_time: 2.8 },
  { agent_type: 'feature', tasks_completed: 67, success_rate: 92.1, avg_time: 4.5 },
  { agent_type: 'doc', tasks_completed: 45, success_rate: 99.1, avg_time: 0.8 },
  { agent_type: 'review', tasks_completed: 134, success_rate: 97.8, avg_time: 1.5 },
]

const mockQualityMetrics: QualityMetrics = {
  first_pass_rate: 78.5,
  code_quality_score: 92.3,
  test_coverage_avg: 85.7,
}

const mockEfficiencyMetrics: EfficiencyMetrics = {
  avg_analysis_time: 0.5,
  avg_design_time: 1.2,
  avg_coding_time: 2.8,
  avg_test_time: 1.1,
}

const mockFunnelData: FunnelData[] = [
  { stage: '需求创建', count: 156, percentage: 100 },
  { stage: '分析完成', count: 142, percentage: 91 },
  { stage: '设计完成', count: 125, percentage: 80 },
  { stage: '编码完成', count: 108, percentage: 69 },
  { stage: '测试通过', count: 95, percentage: 61 },
  { stage: '最终完成', count: 89, percentage: 57 },
]

export const analyticsService = {
  async getDashboardStats(projectId: string, dateRange?: DateRange): Promise<DashboardStats> {
    try {
      const params: Record<string, string> = {}
      if (dateRange) {
        params.start_date = dateRange.start
        params.end_date = dateRange.end
      }
      const response = await api.get<ApiResponse<DashboardStats>>(
        `/projects/${projectId}/analytics/stats`,
        { params }
      )
      return response.data.data
    } catch {
      return mockDashboardStats
    }
  },

  async getTrends(projectId: string, dateRange?: DateRange): Promise<TrendData[]> {
    try {
      const params: Record<string, string> = {}
      if (dateRange) {
        params.start_date = dateRange.start
        params.end_date = dateRange.end
      }
      const response = await api.get<ApiResponse<TrendData[]>>(
        `/projects/${projectId}/analytics/trends`,
        { params }
      )
      return response.data.data
    } catch {
      return mockTrendData
    }
  },

  async getAgentPerformance(projectId: string): Promise<AgentPerformance[]> {
    try {
      const response = await api.get<ApiResponse<AgentPerformance[]>>(
        `/projects/${projectId}/analytics/agents`
      )
      return response.data.data
    } catch {
      return mockAgentPerformance
    }
  },

  async getQualityMetrics(projectId: string): Promise<QualityMetrics> {
    try {
      const response = await api.get<ApiResponse<QualityMetrics>>(
        `/projects/${projectId}/analytics/quality`
      )
      return response.data.data
    } catch {
      return mockQualityMetrics
    }
  },

  async getEfficiencyMetrics(projectId: string): Promise<EfficiencyMetrics> {
    try {
      const response = await api.get<ApiResponse<EfficiencyMetrics>>(
        `/projects/${projectId}/analytics/efficiency`
      )
      return response.data.data
    } catch {
      return mockEfficiencyMetrics
    }
  },

  async getFunnelData(projectId: string): Promise<FunnelData[]> {
    try {
      const response = await api.get<ApiResponse<FunnelData[]>>(
        `/projects/${projectId}/analytics/funnel`
      )
      return response.data.data
    } catch {
      return mockFunnelData
    }
  },

  async exportReport(projectId: string, format: ExportFormat): Promise<Blob> {
    const response = await api.get(`/projects/${projectId}/analytics/export`, {
      params: { format },
      responseType: 'blob',
    })
    return response.data
  },

  async getGlobalStats(): Promise<DashboardStats> {
    try {
      const response = await api.get<ApiResponse<DashboardStats>>('/analytics/global/stats')
      return response.data.data
    } catch {
      return {
        ...mockDashboardStats,
        total_requirements: 458,
        completed: 312,
        in_progress: 98,
        pending_review: 48,
      }
    }
  },
}

export default analyticsService
