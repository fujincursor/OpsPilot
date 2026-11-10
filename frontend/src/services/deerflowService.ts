/**
 * DeerFlow Agent 服务
 * 
 * 提供与后端 DeerFlow API 交互的方法
 */

import api from './api'

export interface AgentStatus {
  available: boolean
  mode: 'deerflow' | 'mock'
  version: string | null
}

export interface ChatRequest {
  message: string
  thread_id?: string
  context?: Record<string, unknown>
}

export interface AgentResponse {
  success: boolean
  message: string
  data: Record<string, unknown>
  thread_id?: string
}

export interface RequirementAnalysisRequest {
  title: string
  description: string
  source?: string
  thread_id?: string
}

export interface SolutionRequest {
  requirement_id: string
  analysis: Record<string, unknown>
  thread_id?: string
}

export interface CodeGenerationRequest {
  solution_id: string
  solution: Record<string, unknown>
  thread_id?: string
}

export interface TestExecutionRequest {
  code_changes: Record<string, unknown>[]
  test_type?: string
  thread_id?: string
}

export interface KnowledgeSearchRequest {
  query: string
  thread_id?: string
}

export interface WorkflowRequest {
  title: string
  description: string
  source?: string
  auto_execute?: boolean
}

interface ApiResponse<T> {
  data: T
}

class DeerFlowService {
  /**
   * 获取 DeerFlow Agent 状态
   */
  async getStatus(): Promise<AgentStatus> {
    const response = await api.get<AgentStatus>('/deerflow/status')
    return response.data
  }

  /**
   * 与 Agent 对话
   */
  async chat(request: ChatRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/chat', request)
    return response.data
  }

  /**
   * 与 Agent 流式对话
   * 返回 EventSource 用于接收 SSE 事件
   */
  chatStream(request: ChatRequest): EventSource {
    const params = new URLSearchParams()
    params.append('message', request.message)
    if (request.thread_id) {
      params.append('thread_id', request.thread_id)
    }
    if (request.context) {
      params.append('context', JSON.stringify(request.context))
    }
    
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    return new EventSource(`${baseUrl}/api/v1/deerflow/chat/stream?${params.toString()}`)
  }

  /**
   * 使用 fetch 进行流式对话（支持 POST 请求）
   */
  async *chatStreamFetch(request: ChatRequest): AsyncGenerator<{ type: string; data: unknown }> {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const response = await fetch(`${baseUrl}/api/v1/deerflow/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            return
          }
          try {
            yield JSON.parse(data)
          } catch {
            // 忽略解析错误
          }
        }
      }
    }
  }

  /**
   * 分析需求
   */
  async analyzeRequirement(request: RequirementAnalysisRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/analyze-requirement', request)
    return response.data
  }

  /**
   * 生成 Bug 修复方案
   */
  async generateBugfix(request: SolutionRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/generate-bugfix', request)
    return response.data
  }

  /**
   * 生成功能设计方案
   */
  async generateFeatureDesign(request: SolutionRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/generate-feature', request)
    return response.data
  }

  /**
   * 生成代码
   */
  async generateCode(request: CodeGenerationRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/generate-code', request)
    return response.data
  }

  /**
   * 执行测试
   */
  async executeTests(request: TestExecutionRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/execute-tests', request)
    return response.data
  }

  /**
   * 搜索知识库
   */
  async searchKnowledge(request: KnowledgeSearchRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/search-knowledge', request)
    return response.data
  }

  /**
   * 启动完整工作流
   */
  async startWorkflow(request: WorkflowRequest): Promise<AgentResponse> {
    const response = await api.post<AgentResponse>('/deerflow/workflow/start', request)
    return response.data
  }
}

export const deerflowService = new DeerFlowService()
export default deerflowService
