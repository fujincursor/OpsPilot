import api from './api'
import type {
  Solution,
  BugFixSolution,
  FeatureDesignSolution,
  SolutionStatus,
  FixStep,
  RegressionRisk,
  ArchitectureDesign,
  ApiDesign,
  DatabaseChange,
} from '../types'

interface ListResponse<T> {
  items: T[]
}

function asText(value: unknown): string {
  if (typeof value === 'string') return value
  if (!value || typeof value !== 'object') return ''
  const record = value as Record<string, unknown>
  const levelLabel = ({ low: '低', medium: '中', high: '高', critical: '严重' } as Record<string, string>)[String(record.level)] || String(record.level || '')
  const scope = typeof record.scope === 'string' ? record.scope : ''
  if (scope.includes('\n') || scope.includes('**') || /^\s*[-|]/m.test(scope)) {
    return [`**影响级别：** ${levelLabel}`, scope].filter((line) => line && !line.endsWith('****')).join('\n\n')
  }
  const lines = [
    record.level ? `**影响级别：** ${levelLabel}` : '',
    scope ? `**影响范围：** ${scope}` : '',
    Array.isArray(record.affected_modules) && record.affected_modules.length
      ? `受影响模块：${record.affected_modules.join('、')}`
      : '',
    Array.isArray(record.affected_services) && record.affected_services.length
      ? `受影响服务：${record.affected_services.join('、')}`
      : '',
    Array.isArray(record.risk_points) && record.risk_points.length
      ? `风险点：${record.risk_points.join('、')}`
      : '',
    Array.isArray(record.mitigation_strategies) && record.mitigation_strategies.length
      ? `缓解策略：${record.mitigation_strategies.join('、')}`
      : '',
  ].filter(Boolean)
  return lines.join('\n\n')
}

function normalizeType(value: unknown): Solution['type'] {
  return value === 'bugfix' || value === 'bug_fix' ? 'bug_fix' : 'feature_design'
}

function normalizeSteps(value: unknown): FixStep[] {
  if (!Array.isArray(value)) return []
  return value.map((step, index) => {
    if (typeof step === 'string') return { order: index + 1, description: step }
    const item = (step || {}) as Record<string, unknown>
    return {
      order: Number(item.order) || index + 1,
      description: String(item.description || ''),
      code_snippet: item.code_snippet ? String(item.code_snippet) : undefined,
      file_path: item.file_path ? String(item.file_path) : undefined,
    }
  })
}

function normalizeRisk(value: unknown): RegressionRisk {
  if (value && typeof value === 'object' && 'level' in value) {
    const item = value as Record<string, unknown>
    const level = item.level === 'high' || item.level === 'low' ? item.level : 'medium'
    return {
      level,
      description: String(item.description || ''),
      affected_areas: Array.isArray(item.affected_areas) ? item.affected_areas.map(String) : [],
    }
  }
  const text = String(value || '')
  const level = text.startsWith('高') ? 'high' : text.startsWith('低') ? 'low' : 'medium'
  const area = text.match(/可能影响([^。；\n]+)/)
  const description = text
    .replace(/^(高|中|低)风险[:：]\s*/, '')
    .replace(/\n*可能影响[^。]*。?\s*$/, '')
    .trim()
  const affected_areas = area
    ? area[1].split(/[、,，]/).map((item) => item.trim()).filter(Boolean)
    : []
  return { level, description, affected_areas }
}

function normalizeArchitecture(value: unknown): ArchitectureDesign {
  if (value && typeof value === 'object' && !Array.isArray(value) && 'components' in value) {
    const design = value as ArchitectureDesign
    return {
      overview: design.overview || '',
      components: Array.isArray(design.components) ? design.components : [],
      diagram: design.diagram,
    }
  }
  const components = Array.isArray(value) ? value : []
  return {
    overview: '',
    components: components.map((item) => {
      const component = (item || {}) as Record<string, unknown>
      return {
        name: String(component.name || '未命名组件'),
        description: String(component.description || component.type || ''),
        responsibilities: [
          ...(Array.isArray(component.responsibilities) ? component.responsibilities.map(String) : []),
          ...(Array.isArray(component.interfaces) ? component.interfaces.map(String) : []),
        ],
      }
    }),
  }
}

function asBody(value: unknown): string | undefined {
  if (!value) return undefined
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2)
}

function normalizeApis(value: unknown): ApiDesign[] {
  if (!Array.isArray(value)) return []
  return value.map((item) => {
    const apiItem = (item || {}) as Record<string, unknown>
    const method = String(apiItem.method || 'GET').toUpperCase()
    const safeMethod = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].includes(method) ? method : 'GET'
    return {
      method: safeMethod as ApiDesign['method'],
      endpoint: String(apiItem.endpoint || apiItem.path || ''),
      description: String(apiItem.description || ''),
      request_body: asBody(apiItem.request_body),
      response_body: asBody(apiItem.response_body),
    }
  })
}

function normalizeDatabaseChanges(value: unknown): DatabaseChange[] {
  if (!Array.isArray(value)) return []
  return value.map((item) => {
    const change = (item || {}) as Record<string, unknown>
    const type = String(change.type || change.change_type || 'alter_table')
    const safeType = ['create_table', 'alter_table', 'create_index', 'migration'].includes(type)
      ? type
      : 'alter_table'
    return {
      type: safeType as DatabaseChange['type'],
      table_name: String(change.table_name || ''),
      description: String(change.description || ''),
      sql: change.sql ? String(change.sql) : change.sql_migration ? String(change.sql_migration) : undefined,
    }
  })
}

function normalizeSolution(raw: BugFixSolution | FeatureDesignSolution | Solution): BugFixSolution | FeatureDesignSolution {
  const record = raw as unknown as Record<string, unknown>
  const type = normalizeType(record.type)
  const base = {
    ...raw,
    type,
    content: typeof record.content === 'string' ? record.content : '',
    impact_analysis: asText(record.impact_analysis),
    affected_files: Array.isArray(record.affected_files) ? record.affected_files.map(String) : [],
    created_by_agent: String(record.created_by_agent || 'Agent'),
    skill_key: typeof record.skill_key === 'string' ? record.skill_key : '',
    skill_name: typeof record.skill_name === 'string' ? record.skill_name : '',
  }
  if (type === 'bug_fix') {
    return {
      ...base,
      type: 'bug_fix',
      root_cause: String(record.root_cause || ''),
      fix_steps: normalizeSteps(record.fix_steps),
      regression_risk: normalizeRisk(record.regression_risk),
    }
  }
  return {
    ...base,
    type: 'feature_design',
    architecture: normalizeArchitecture(record.architecture),
    api_design: normalizeApis(record.api_design),
    database_changes: normalizeDatabaseChanges(record.database_changes),
    dependencies: Array.isArray(record.dependencies) ? record.dependencies.map(String) : [],
  }
}

export const solutionService = {
  async generateSolution(reqId: string): Promise<Solution> {
    const response = await api.post<BugFixSolution | FeatureDesignSolution>(
      `/requirements/${reqId}/solutions/generate`,
      undefined,
      { timeout: 180000 },
    )
    return normalizeSolution(response.data)
  },

  async getSolutions(reqId: string): Promise<Solution[]> {
    const response = await api.get<ListResponse<Solution>>(`/requirements/${reqId}/solutions`)
    return response.data.items.map((item) => normalizeSolution(item))
  },

  async getSolution(solutionId: string): Promise<BugFixSolution | FeatureDesignSolution> {
    const response = await api.get<BugFixSolution | FeatureDesignSolution>(`/solutions/${solutionId}`)
    return normalizeSolution(response.data)
  },

  async updateSolutionStatus(solutionId: string, status: SolutionStatus, comment?: string): Promise<Solution> {
    const response = await api.patch<Solution>(`/solutions/${solutionId}/status`, {
      status,
      review_comment: comment,
    })
    return normalizeSolution(response.data)
  },

  async regenerateSolution(solutionId: string): Promise<Solution> {
    const response = await api.post<Solution>(`/solutions/${solutionId}/regenerate`, undefined, { timeout: 180000 })
    return normalizeSolution(response.data)
  },
}

export default solutionService
