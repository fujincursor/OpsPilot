"""opspilot.db 的关系表。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _pk() -> Mapped[str]:
    return mapped_column(String(36), primary_key=True)


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = _pk()
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    repo_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    toolchain: Mapped[str] = mapped_column(Text, nullable=False, default="")
    code_origin: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    code_status: Mapped[str] = mapped_column(String(32), nullable=False, default="empty")
    code_branch: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    code_revision: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    code_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    code_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ProjectMemberRow(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="developer")


class ProjectSkillRow(Base):
    __tablename__ = "project_skills"
    __table_args__ = (UniqueConstraint("project_id", "skill_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    skill_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    agent: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ProjectProfileRow(Base):
    __tablename__ = "project_profiles"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    overview: Mapped[str] = mapped_column(Text, nullable=False, default="")
    architecture: Mapped[str] = mapped_column(Text, nullable=False, default="")
    directory_layout: Mapped[str] = mapped_column(Text, nullable=False, default="")
    key_modules: Mapped[str] = mapped_column(Text, nullable=False, default="")
    config_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    runbook: Mapped[str] = mapped_column(Text, nullable=False, default="")


class SandboxSettingsRow(Base):
    __tablename__ = "sandbox_settings"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    backend: Mapped[str] = mapped_column(String(32), nullable=False, default="local")
    image: Mapped[str] = mapped_column(String(200), nullable=False, default="python:3.11-slim")
    memory_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    cpu: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    disk_gb: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    network_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="disabled")
    python_requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    run_as_non_root: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    disable_privileged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    read_only_root: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    disable_setuid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    seccomp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kubeconfig_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="default")
    kubeconfig: Mapped[str] = mapped_column(Text, nullable=False, default="")
    namespace: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    service_account: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    e2b_api_key: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    e2b_template: Mapped[str] = mapped_column(String(100), nullable=False, default="python-3.11")


class SandboxAllowedDomainRow(Base):
    __tablename__ = "sandbox_allowed_domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    domain: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SandboxSystemToolRow(Base):
    __tablename__ = "sandbox_system_tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class RequirementRow(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = _pk()
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="web")
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="feature")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    assignee: Mapped[str | None] = mapped_column(String(50))
    created_by: Mapped[str | None] = mapped_column(String(50))
    analysis_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    session_id: Mapped[str | None] = mapped_column(String(36))
    auto_advance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rework_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RequirementKeywordRow(Base):
    __tablename__ = "requirement_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SolutionRow(Base):
    __tablename__ = "solutions"

    id: Mapped[str] = _pk()
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    impact_level: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    impact_scope: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_agent: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    skill_key: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    reviewed_by: Mapped[str | None] = mapped_column(String(50))
    review_comment: Mapped[str | None] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False, default="")
    regression_risk: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rollback_plan: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SolutionTextItemRow(Base):
    """方案里的有序文本项。

    item_kind 取值：affected_file、fix_step、test_suggestion、dependency、phase、
    impact_module、impact_service、impact_risk、impact_mitigation。
    """

    __tablename__ = "solution_text_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solution_id: Mapped[str] = mapped_column(ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False)
    item_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SolutionComponentRow(Base):
    __tablename__ = "solution_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solution_id: Mapped[str] = mapped_column(ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    component_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SolutionComponentRefRow(Base):
    __tablename__ = "solution_component_refs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("solution_components.id", ondelete="CASCADE"), nullable=False)
    ref_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SolutionApiEndpointRow(Base):
    __tablename__ = "solution_api_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solution_id: Mapped[str] = mapped_column(ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    request_body: Mapped[str | None] = mapped_column(Text)
    response_body: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SolutionDatabaseChangeRow(Base):
    __tablename__ = "solution_database_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solution_id: Mapped[str] = mapped_column(ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False)
    change_type: Mapped[str] = mapped_column(String(64), nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sql_migration: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SolutionNfrRow(Base):
    __tablename__ = "solution_nfr"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solution_id: Mapped[str] = mapped_column(ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")


class CodegenTaskRow(Base):
    __tablename__ = "codegen_tasks"

    id: Mapped[str] = _pk()
    solution_id: Mapped[str] = mapped_column(ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    language: Mapped[str] = mapped_column(String(32), nullable=False, default="python")
    error_message: Mapped[str | None] = mapped_column(Text)
    sandbox_id: Mapped[str | None] = mapped_column(String(80))
    sandbox_profile: Mapped[str | None] = mapped_column(Text)
    lint_json: Mapped[str | None] = mapped_column(Text)
    mr_json: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class CodeFileRow(Base):
    __tablename__ = "code_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("codegen_tasks.id", ondelete="CASCADE"), nullable=False)
    step_index: Mapped[int | None] = mapped_column(Integer)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language: Mapped[str] = mapped_column(String(32), nullable=False, default="python")
    action: Mapped[str] = mapped_column(String(32), nullable=False, default="create")
    diff_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CodegenStepRow(Base):
    __tablename__ = "codegen_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("codegen_tasks.id", ondelete="CASCADE"), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error_message: Mapped[str | None] = mapped_column(Text)


class CodegenLocationRow(Base):
    __tablename__ = "codegen_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("codegen_tasks.id", ondelete="CASCADE"), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CodegenAppliedPathRow(Base):
    __tablename__ = "codegen_applied_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("codegen_tasks.id", ondelete="CASCADE"), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TestTaskRow(Base):
    __tablename__ = "test_tasks"

    id: Mapped[str] = _pk()
    codegen_task_id: Mapped[str] = mapped_column(ForeignKey("codegen_tasks.id", ondelete="CASCADE"), nullable=False)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    sandbox_id: Mapped[str | None] = mapped_column(String(80))
    sandbox_profile: Mapped[str | None] = mapped_column(Text)
    coverage_json: Mapped[str | None] = mapped_column(Text)
    ci_pipeline_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class TestCaseRow(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = _pk()
    task_id: Mapped[str] = mapped_column(ForeignKey("test_tasks.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="unit")
    code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expected_result: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    target_function: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TestResultRow(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("test_tasks.id", ondelete="CASCADE"), nullable=False)
    test_case_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    actual_result: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TestReportRow(Base):
    __tablename__ = "test_reports"

    task_id: Mapped[str] = mapped_column(ForeignKey("test_tasks.id", ondelete="CASCADE"), primary_key=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    coverage_json: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TestReportFailureRow(Base):
    __tablename__ = "test_report_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("test_reports.task_id", ondelete="CASCADE"), nullable=False)
    case_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CiPipelineRow(Base):
    __tablename__ = "ci_pipelines"

    id: Mapped[str] = mapped_column(ForeignKey("test_tasks.id", ondelete="CASCADE"), primary_key=True)
    pipeline_id: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    url: Mapped[str | None] = mapped_column(String(500))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class CiStageRow(Base):
    __tablename__ = "ci_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_row_id: Mapped[str] = mapped_column(ForeignKey("ci_pipelines.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ReviewItemRow(Base):
    __tablename__ = "review_items"

    id: Mapped[str] = _pk()
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    item_id: Mapped[str] = mapped_column(String(36), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requirement_id: Mapped[str | None] = mapped_column(String(36))
    session_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    reviewer: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime)


class ReviewCommentRow(Base):
    __tablename__ = "review_comments"

    id: Mapped[str] = _pk()
    review_item_id: Mapped[str] = mapped_column(ForeignKey("review_items.id", ondelete="CASCADE"), nullable=False)
    author: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ReviewDecisionRow(Base):
    __tablename__ = "review_decisions"

    id: Mapped[str] = _pk()
    review_item_id: Mapped[str] = mapped_column(ForeignKey("review_items.id", ondelete="CASCADE"), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ReviewHistoryRow(Base):
    __tablename__ = "review_history"

    id: Mapped[str] = _pk()
    review_item_id: Mapped[str] = mapped_column(ForeignKey("review_items.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class NotificationRow(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = _pk()
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    review_item_id: Mapped[str | None] = mapped_column(String(36))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ChatSessionRow(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = _pk()
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ChatMessageRow(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = _pk()
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sender: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str | None] = mapped_column(String(32))
    knowledge_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    knowledge_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    classification_json: Mapped[str | None] = mapped_column(Text)
    review_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class KnowledgeBaseRow(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = _pk()
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="doc")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    index_trigger: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    update_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="incremental")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class KnowledgeIndexPathRow(Base):
    __tablename__ = "knowledge_index_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_base_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    path: Mapped[str] = mapped_column(String(300), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class KnowledgeIndexJobRow(Base):
    __tablename__ = "knowledge_index_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_base_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = _pk()
    knowledge_base_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_type: Mapped[str | None] = mapped_column(String(32))
    embedding_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    embedding_model: Mapped[str | None] = mapped_column(String(100))
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SkillCatalogRow(Base):
    __tablename__ = "skill_catalog"

    skill_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    agent: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")


class AgentPromptTemplateRow(Base):
    __tablename__ = "agent_prompt_templates"

    agent_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)


class AgentRow(Base):
    __tablename__ = "agents"

    id: Mapped[str] = _pk()
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="deepseek-v4")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=4096)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AgentSkillRow(Base):
    __tablename__ = "agent_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    skill_key: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CompletionRecordRow(Base):
    __tablename__ = "completion_records"

    id: Mapped[str] = _pk()
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    solution_id: Mapped[str | None] = mapped_column(String(36))
    codegen_task_id: Mapped[str | None] = mapped_column(String(36))
    test_task_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CompletionLessonRow(Base):
    __tablename__ = "completion_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(ForeignKey("completion_records.id", ondelete="CASCADE"), nullable=False)
    lesson: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CaseStudyRow(Base):
    __tablename__ = "case_studies"

    id: Mapped[str] = _pk()
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    problem: Mapped[str] = mapped_column(Text, nullable=False, default="")
    solution_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    implementation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    results: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CaseTagRow(Base):
    __tablename__ = "case_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("case_studies.id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CaseDocumentRow(Base):
    __tablename__ = "case_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("case_studies.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class KnowledgeUpdateRow(Base):
    __tablename__ = "knowledge_updates"

    id: Mapped[str] = _pk()
    knowledge_base_id: Mapped[str | None] = mapped_column(String(36))
    document_id: Mapped[str | None] = mapped_column(String(36))
    update_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_requirement_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
