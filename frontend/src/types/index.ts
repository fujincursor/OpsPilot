export interface Project {
  id: string
  name: string
  description: string
  repo_url: string
  status: 'active' | 'inactive' | 'archived'
  created_at: string
  updated_at: string
}

export interface AgentConfig {
  id: string
  project_id: string
  agent_type: 'lead' | 'bugfix' | 'feature' | 'doc' | 'review'
  name: string
  description: string
  model_name: string
  temperature: number
  max_tokens: number
  skills: string[]
  enabled: boolean
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'developer' | 'viewer'
}

export interface CreateProjectRequest {
  name: string
  description: string
  repo_url: string
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  repo_url?: string
  status?: Project['status']
}

export interface UpdateAgentConfigRequest {
  model_name?: string
  temperature?: number
  max_tokens?: number
  skills?: string[]
  enabled?: boolean
}

export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

export type KnowledgeStatus = 'pending' | 'indexing' | 'ready' | 'error'
export type KnowledgeType = 'doc' | 'code' | 'faq'

export interface KnowledgeBase {
  id: string
  project_id: string
  name: string
  description: string
  type: KnowledgeType
  status: KnowledgeStatus
  document_count: number
  created_at: string
}

export interface Document {
  id: string
  knowledge_base_id: string
  title: string
  content: string
  file_path: string
  file_type: string
  embedding_status: KnowledgeStatus
  created_at: string
}

export interface CreateKnowledgeBaseRequest {
  name: string
  description: string
  type: KnowledgeType
}

export interface SearchResult {
  document_id: string
  title: string
  content: string
  score: number
  knowledge_base_name: string
}

export interface KnowledgeStatusSummary {
  total: number
  pending: number
  indexing: number
  ready: number
  error: number
}

export type RequirementType = 'bug' | 'feature' | 'question'
export type RequirementStatus = 'pending' | 'analyzing' | 'designing' | 'reviewing' | 'coding' | 'testing' | 'completed' | 'closed'
export type RequirementPriority = 'low' | 'medium' | 'high' | 'critical'

export interface AnalysisResult {
  type: RequirementType
  priority: RequirementPriority
  keywords: string[]
  confidence: number
}

export interface Requirement {
  id: string
  project_id: string
  title: string
  description: string
  source: string
  type: RequirementType
  priority: RequirementPriority
  status: RequirementStatus
  assignee?: string
  created_by: string
  analysis_result?: AnalysisResult
  created_at: string
  updated_at?: string
}

export interface CreateRequirementRequest {
  title: string
  description: string
  source?: string
  type?: RequirementType
  priority?: RequirementPriority
}

export interface UpdateRequirementRequest {
  title?: string
  description?: string
  type?: RequirementType
  priority?: RequirementPriority
  assignee?: string
}

export interface RequirementFilters {
  type?: RequirementType
  status?: RequirementStatus
  priority?: RequirementPriority
  assignee?: string
}

export interface StatusHistoryItem {
  status: RequirementStatus
  changed_at: string
  changed_by: string
  comment?: string
}

export type SolutionStatus = 'draft' | 'pending_review' | 'approved' | 'rejected' | 'implemented'
export type SolutionType = 'bug_fix' | 'feature_design'

export interface Solution {
  id: string
  requirement_id: string
  type: SolutionType
  title: string
  content: string
  impact_analysis: string
  affected_files: string[]
  status: SolutionStatus
  created_by_agent: string
  reviewed_by?: string
  created_at: string
}

export interface BugFixSolution extends Solution {
  type: 'bug_fix'
  root_cause: string
  fix_steps: FixStep[]
  regression_risk: RegressionRisk
}

export interface FixStep {
  order: number
  description: string
  code_snippet?: string
  file_path?: string
}

export interface RegressionRisk {
  level: 'low' | 'medium' | 'high'
  description: string
  affected_areas: string[]
}

export interface FeatureDesignSolution extends Solution {
  type: 'feature_design'
  architecture: ArchitectureDesign
  api_design: ApiDesign[]
  database_changes: DatabaseChange[]
  dependencies: string[]
}

export interface ArchitectureDesign {
  overview: string
  components: ArchitectureComponent[]
  diagram?: string
}

export interface ArchitectureComponent {
  name: string
  description: string
  responsibilities: string[]
}

export interface ApiDesign {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  endpoint: string
  description: string
  request_body?: string
  response_body?: string
}

export interface DatabaseChange {
  type: 'create_table' | 'alter_table' | 'create_index' | 'migration'
  table_name: string
  description: string
  sql?: string
}

export interface GenerateSolutionRequest {
  requirement_id: string
}

export interface UpdateSolutionStatusRequest {
  status: SolutionStatus
  comment?: string
}

// Review Types
export type ReviewStatus = 'pending' | 'in_review' | 'approved' | 'rejected' | 'revision_requested'
export type ReviewItemType = 'solution' | 'code' | 'test'

export interface ReviewItem {
  id: string
  item_type: ReviewItemType
  item_id: string
  project_id: string
  title: string
  description: string
  status: ReviewStatus
  priority: RequirementPriority
  reviewer?: string
  comments_count: number
  created_at: string
  due_at?: string
}

export interface ReviewComment {
  id: string
  review_item_id: string
  author: string
  content: string
  created_at: string
}

export interface ReviewDecision {
  id: string
  review_item_id: string
  decision: 'approved' | 'rejected' | 'revision_requested'
  reviewer: string
  reason: string
  created_at: string
}

export type NotificationType = 'review_assigned' | 'review_completed' | 'comment_added' | 'revision_requested'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  read: boolean
  created_at: string
  link?: string
}

export interface ReviewFilters {
  item_type?: ReviewItemType
  status?: ReviewStatus
  priority?: RequirementPriority
}

// Code Generation Types
export type CodeGenStatus = 'pending' | 'generating' | 'linting' | 'completed' | 'failed'

export type DiffLineType = 'add' | 'remove' | 'context'

export interface DiffLine {
  type: DiffLineType
  content: string
  line_number: number
}

export interface LintResult {
  passed: boolean
  errors: LintMessage[]
  warnings: LintMessage[]
}

export interface LintMessage {
  file: string
  line: number
  column: number
  message: string
  rule?: string
}

export type CodeFileAction = 'create' | 'modify' | 'delete'

export interface CodeFile {
  path: string
  content: string
  language: string
  action: CodeFileAction
  diff?: DiffLine[]
}

export interface CodeGenTask {
  id: string
  solution_id: string
  requirement_id: string
  status: CodeGenStatus
  language: string
  files: CodeFile[]
  lint_result?: LintResult
  error_message?: string
  created_at: string
  updated_at?: string
}

export interface CreateCodeGenTaskRequest {
  solution_id: string
}

export interface CodeGenTaskSummary {
  id: string
  status: CodeGenStatus
  files_count: number
  created_at: string
}

// Test Types
export type TestStatus = 'pending' | 'generating' | 'running' | 'completed' | 'failed'
export type TestCaseType = 'unit' | 'integration' | 'e2e'
export type TestResultStatus = 'passed' | 'failed' | 'skipped'

export interface TestCase {
  id: string
  name: string
  description: string
  type: TestCaseType
  code: string
  expected_result: string
}

export interface TestResult {
  test_case_id: string
  status: TestResultStatus
  actual_result: string
  error_message?: string
  duration: number
}

export interface TestReport {
  task_id: string
  total: number
  passed: number
  failed: number
  skipped: number
  coverage_percent: number
  duration: number
}

export interface TestTask {
  id: string
  codegen_task_id: string
  requirement_id: string
  status: TestStatus
  test_cases: TestCase[]
  results: TestResult[]
  coverage: number
  created_at: string
}

export interface TestTaskSummary {
  id: string
  status: TestStatus
  total_cases: number
  passed: number
  failed: number
  created_at: string
}

export interface CreateTestTaskRequest {
  codegen_task_id: string
}
