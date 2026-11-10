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
} from '../types'

export interface GlobalStats {
  total_projects: number
  total_requirements: number
  total_completed: number
  active_agents: number
  avg_completion_rate: number
  avg_quality_score: number
}

interface TrendResponse {
  data: Array<{ date: string; count: number; trend_type: TrendData['type'] | 'in_progress' }>
}

interface AgentPerformanceResponse {
  items: Array<AgentPerformance & { agent_name?: string }>
}

interface FunnelResponse {
  stages: FunnelData[]
}

function toDateRangeParams(dateRange?: DateRange): Record<string, string> {
  if (!dateRange) return { date_range: '30d' }
  const start = new Date(dateRange.start)
  const end = new Date(dateRange.end)
  const days = Math.round((end.getTime() - start.getTime()) / 86400000)
  if (days <= 7) return { date_range: '7d' }
  if (days <= 30) return { date_range: '30d' }
  if (days <= 90) return { date_range: '90d' }
  return { date_range: 'custom', start_date: dateRange.start, end_date: dateRange.end }
}

export const analyticsService = {
  async getDashboardStats(projectId: string, dateRange?: DateRange): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>(`/projects/${projectId}/analytics/dashboard`, {
      params: toDateRangeParams(dateRange),
    })
    return response.data
  },

  async getTrends(projectId: string, dateRange?: DateRange): Promise<TrendData[]> {
    const response = await api.get<TrendResponse>(`/projects/${projectId}/analytics/trends`, {
      params: toDateRangeParams(dateRange),
    })
    return response.data.data
      .filter((item) => item.trend_type === 'created' || item.trend_type === 'completed')
      .map((item) => ({
        date: item.date,
        count: item.count,
        type: item.trend_type as TrendData['type'],
      }))
  },

  async getAgentPerformance(projectId: string): Promise<AgentPerformance[]> {
    const response = await api.get<AgentPerformanceResponse>(`/projects/${projectId}/analytics/agents`)
    return response.data.items
  },

  async getQualityMetrics(projectId: string): Promise<QualityMetrics> {
    const response = await api.get<QualityMetrics>(`/projects/${projectId}/analytics/quality`)
    return response.data
  },

  async getEfficiencyMetrics(projectId: string): Promise<EfficiencyMetrics> {
    const response = await api.get<EfficiencyMetrics>(`/projects/${projectId}/analytics/efficiency`)
    return response.data
  },

  async getFunnelData(projectId: string): Promise<FunnelData[]> {
    const response = await api.get<FunnelResponse>(`/projects/${projectId}/analytics/funnel`)
    return response.data.stages
  },

  async exportReport(projectId: string, _format: ExportFormat): Promise<Blob> {
    const response = await api.post(`/projects/${projectId}/analytics/export`, {
      export_format: 'json',
      date_range: '30d',
    })
    return new Blob([JSON.stringify(response.data.data ?? response.data, null, 2)], {
      type: 'application/json',
    })
  },

  async getGlobalStats(): Promise<GlobalStats> {
    const response = await api.get<GlobalStats>('/analytics/global')
    return response.data
  },
}

export default analyticsService
