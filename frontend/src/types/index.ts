export interface ProjectSkill {
  key: string
  name: string
  description: string
  agent?: string
  enabled: boolean
  usage_count?: number
}

export interface ProjectProfile {
  overview: string
  architecture: string
  directory_layout: string
  key_modules: string
  config_notes: string
  runbook: string
}

export interface ProjectMember {
  username: string
  role: string
}

export interface SandboxSettings {
  backend: string
  memory_mb: number
  cpu: number
  timeout_seconds: number
  network_policy: string
  allowed_domains: string[]
  run_as_non_root: boolean
}

export interface Project {
  id: string
  name: string
  description: string
  repo_url: string
  status: 'active' | 'inactive' | 'archived'
  skills?: ProjectSkill[]
  sandbox?: SandboxSettings
  profile?: ProjectProfile
  members?: ProjectMember[]
  prompt_template?: string
  toolchain?: string
  created_at: string
  updated_at: string
}

export interface AgentConfig {
  id: string
  project_id: string
  agent_type: 'lead' | 'bugfix' | 'feature' | 'doc' | 'review' | 'codegen' | 'test'
  name: string
  description: string
  model_name: string
  temperature: number
  max_tokens: number
  skills: string[]
  prompt?: string
  enabled: boolean
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'developer' | 'operator' | 'reviewer' | 'viewer'
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
  skills?: ProjectSkill[]
  sandbox?: SandboxSettings
  profile?: ProjectProfile
  members?: ProjectMember[]
  prompt_template?: string
  toolchain?: string
}

export interface UpdateAgentConfigRequest {
  model_name?: string
  temperature?: number
  max_tokens?: number
  skills?: string[]
  prompt?: string
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
export type EmbeddingStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type KnowledgeType = 'doc' | 'code' | 'faq'

export interface KnowledgeBase {
  id: string
  project_id: string
  name: string
  description: string
  type: KnowledgeType
  status: KnowledgeStatus
  document_count: number
  index_paths?: string[]
  index_trigger?: string
  update_policy?: string
  index_jobs?: Array<{ id: string; status: string; message: string; created_at: string }>
  created_at: string
}

export interface Document {
  id: string
  knowledge_base_id: string
  title: string
  content: string
  file_path: string
  file_type: string
  embedding_status: EmbeddingStatus
  embedding_model?: string
  chunk_count?: number
  error_message?: string
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
  failure_reason?: string
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
  skill_key?: string
  skill_name?: string
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
  session_id?: string
  requirement_id?: string
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
  project_id?: string
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

export type CodeFileAction = 'create' | 'modify' | 'delete' | 'view'

export interface CodeFile {
  path: string
  content: string
  language: string
  action: CodeFileAction
  diff?: DiffLine[]
}

export type CodeGenStepStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface CodeLocation {
  path: string
  line: number
  snippet: string
  reason: string
}

export interface CodeGenStep {
  index: number
  title: string
  status: CodeGenStepStatus
  output: string
  locations?: CodeLocation[]
  files?: CodeFile[]
  error_message?: string
}

export interface CodeGenTask {
  id: string
  solution_id: string
  requirement_id: string
  status: CodeGenStatus
  language: string
  files: CodeFile[]
  steps?: CodeGenStep[]
  lint_result?: LintResult
  error_message?: string
  applied_at?: string
  applied_paths?: string[]
  sandbox_profile?: string
  created_at: string
  updated_at?: string
}

export interface CreateCodeGenTaskRequest {
  solution_id: string
}

export interface CodeGenTaskSummary {
  id: string
  status: CodeGenStatus
  files_count?: number
  files?: CodeFile[]
  steps?: CodeGenStep[]
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
  duration?: number
  duration_ms?: number
}

export interface CIStage {
  name: string
  status: string
  detail?: string
}

export interface CIPipeline {
  pipeline_id: string
  status: string
  triggered_at: string
  completed_at?: string | null
  stages: CIStage[]
}

export interface TestReport {
  task_id: string
  total: number
  passed: number
  failed: number
  skipped: number
  coverage_percent: number
  duration?: number
  duration_ms?: number
}

export interface TestTask {
  id: string
  codegen_task_id: string
  requirement_id: string
  status: TestStatus
  test_cases: TestCase[]
  results: TestResult[]
  coverage: number
  sandbox_profile?: string
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

// Dashboard & Analytics Types
export interface DashboardStats {
  total_requirements: number
  completed: number
  in_progress: number
  pending_review: number
  avg_completion_time: number
}

export interface TrendData {
  date: string
  count: number
  type: 'created' | 'completed' | 'closed'
}

export interface AgentPerformance {
  agent_type: 'lead' | 'bugfix' | 'feature' | 'doc' | 'review' | 'codegen' | 'test'
  tasks_completed: number
  success_rate: number
  avg_time: number
}

export interface QualityMetrics {
  first_pass_rate: number
  code_quality_score: number
  test_coverage_avg: number
}

export interface EfficiencyMetrics {
  avg_analysis_time: number
  avg_design_time: number
  avg_coding_time: number
  avg_test_time: number
}

export interface FunnelData {
  stage: string
  count: number
  percentage: number
}

export interface DateRange {
  start: string
  end: string
}

export type ExportFormat = 'pdf' | 'excel' | 'csv'
