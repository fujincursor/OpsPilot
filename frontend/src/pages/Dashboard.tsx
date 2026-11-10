import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { analyticsService, projectService } from '../services'
import {
  StatCard,
  TrendChart,
  AgentPerformanceCard,
  QualityCard,
  EfficiencyCard,
  FunnelChart,
  DateRangePicker,
} from '../components/Dashboard'
import type {
  DashboardStats,
  TrendData,
  AgentPerformance,
  QualityMetrics,
  EfficiencyMetrics,
  FunnelData,
  DateRange,
  Project,
  ExportFormat,
} from '../types'

function getDefaultDateRange(): DateRange {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 7)
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  }
}

export default function Dashboard() {
  const { id: projectId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState<Project | null>(null)
  const [dateRange, setDateRange] = useState<DateRange>(getDefaultDateRange())
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [trends, setTrends] = useState<TrendData[]>([])
  const [agentPerformance, setAgentPerformance] = useState<AgentPerformance[]>([])
  const [qualityMetrics, setQualityMetrics] = useState<QualityMetrics | null>(null)
  const [efficiencyMetrics, setEfficiencyMetrics] = useState<EfficiencyMetrics | null>(null)
  const [funnelData, setFunnelData] = useState<FunnelData[]>([])
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    if (projectId) {
      loadData()
    }
  }, [projectId, dateRange])

  const loadData = async () => {
    if (!projectId) return
    setLoading(true)
    
    try {
      const [
        projectData,
        statsData,
        trendsData,
        agentData,
        qualityData,
        efficiencyData,
        funnelDataResult,
      ] = await Promise.all([
        projectService.getProject(projectId),
        analyticsService.getDashboardStats(projectId, dateRange),
        analyticsService.getTrends(projectId, dateRange),
        analyticsService.getAgentPerformance(projectId),
        analyticsService.getQualityMetrics(projectId),
        analyticsService.getEfficiencyMetrics(projectId),
        analyticsService.getFunnelData(projectId),
      ])
      
      setProject(projectData)
      setStats(statsData)
      setTrends(trendsData)
      setAgentPerformance(agentData)
      setQualityMetrics(qualityData)
      setEfficiencyMetrics(efficiencyData)
      setFunnelData(funnelDataResult)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format: ExportFormat) => {
    if (!projectId) return
    setExporting(true)
    
    try {
      const blob = await analyticsService.exportReport(projectId, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dashboard-report-${projectId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export report:', error)
    } finally {
      setExporting(false)
    }
  }

  const calculateChange = (current: number, total: number) => {
    if (total === 0) return 0
    return Math.round((current / total) * 100)
  }

  if (loading) {
    return (
      <div className="p-6 bg-gray-50 min-h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <span className="text-gray-500">加载数据中...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <button 
                onClick={() => navigate(`/projects/${projectId}`)}
                className="hover:text-primary transition-colors"
              >
                {project?.name || '项目'}
              </button>
              <span>/</span>
              <span>运营看板</span>
            </div>
            <h1 className="text-2xl font-semibold text-gray-800">📊 运营数据看板</h1>
          </div>
          
          <div className="flex items-center gap-3">
            <DateRangePicker value={dateRange} onChange={setDateRange} />
            <div className="relative group">
              <button
                disabled={exporting}
                className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {exporting ? (
                  <span className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></span>
                ) : (
                  '📥'
                )}
                导出报告
              </button>
              <div className="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 hidden group-hover:block z-10 min-w-[120px]">
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full px-4 py-2 text-sm text-left text-gray-600 hover:bg-gray-50"
                >
                  导出 PDF
                </button>
                <button
                  onClick={() => handleExport('excel')}
                  className="w-full px-4 py-2 text-sm text-left text-gray-600 hover:bg-gray-50"
                >
                  导出 Excel
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full px-4 py-2 text-sm text-left text-gray-600 hover:bg-gray-50"
                >
                  导出 CSV
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="总需求数"
              value={stats.total_requirements}
              icon="📋"
              gradient="blue"
              change={12}
              changeLabel="较上周"
            />
            <StatCard
              title="已完成"
              value={stats.completed}
              icon="✅"
              gradient="green"
              change={calculateChange(stats.completed, stats.total_requirements)}
              changeLabel="完成率"
            />
            <StatCard
              title="进行中"
              value={stats.in_progress}
              icon="⚡"
              gradient="orange"
              change={calculateChange(stats.in_progress, stats.total_requirements)}
              changeLabel="占比"
            />
            <StatCard
              title="待审核"
              value={stats.pending_review}
              icon="👀"
              gradient="purple"
              change={-5}
              changeLabel="较上周"
            />
          </div>
        )}

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <TrendChart data={trends} title="需求趋势" height={220} />
          <AgentPerformanceCard data={agentPerformance} title="Agent 效率对比" />
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {qualityMetrics && (
            <QualityCard data={qualityMetrics} title="质量指标" />
          )}
          {efficiencyMetrics && (
            <EfficiencyCard data={efficiencyMetrics} title="效率指标" />
          )}
        </div>

        {/* Funnel Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FunnelChart data={funnelData} title="需求完成漏斗" />
          
          {/* Summary Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-base font-semibold text-gray-800 mb-4">📈 数据洞察</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                <span className="text-lg">💡</span>
                <div>
                  <div className="text-sm font-medium text-green-800">高效能提示</div>
                  <div className="text-xs text-green-600 mt-0.5">
                    Lead Agent 本周处理效率提升 15%，建议继续保持当前工作流程。
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
                <span className="text-lg">⚠️</span>
                <div>
                  <div className="text-sm font-medium text-amber-800">待关注</div>
                  <div className="text-xs text-amber-600 mt-0.5">
                    代码生成阶段耗时占比较高（50%），可考虑优化生成策略。
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                <span className="text-lg">📊</span>
                <div>
                  <div className="text-sm font-medium text-blue-800">周期对比</div>
                  <div className="text-xs text-blue-600 mt-0.5">
                    本周完成需求较上周增长 8%，整体效率持续改善。
                  </div>
                </div>
              </div>
              
              {stats && (
                <div className="pt-3 border-t border-gray-100">
                  <div className="text-xs text-gray-500 mb-2">平均完成时间</div>
                  <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold text-primary">
                      {stats.avg_completion_time}
                    </span>
                    <span className="text-gray-500 mb-1">小时</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
