"""代码生成模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CodeGenStatus(str, Enum):
    """代码生成任务状态"""
    PENDING = "pending"
    GENERATING = "generating"
    LINTING = "linting"
    COMPLETED = "completed"
    FAILED = "failed"


class FileAction(str, Enum):
    """文件操作类型"""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class CodeFile(BaseModel):
    """代码文件模型"""
    path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    content: str = Field(default="", description="文件内容")
    language: str = Field(default="python", description="编程语言")
    action: FileAction = Field(default=FileAction.CREATE, description="文件操作类型")

    class Config:
        from_attributes = True


class LintError(BaseModel):
    """Lint 错误详情"""
    file: str = Field(..., description="文件路径")
    line: int = Field(..., description="行号")
    column: int = Field(default=0, description="列号")
    code: str = Field(default="", description="错误代码")
    message: str = Field(..., description="错误消息")
    severity: str = Field(default="error", description="严重级别: error/warning")


class LintResult(BaseModel):
    """Lint 检查结果"""
    passed: bool = Field(default=True, description="是否通过检查")
    errors: List[LintError] = Field(default_factory=list, description="错误列表")
    warnings: List[LintError] = Field(default_factory=list, description="警告列表")
    error_count: int = Field(default=0, description="错误数量")
    warning_count: int = Field(default=0, description="警告数量")

    class Config:
        from_attributes = True


class CodeDiff(BaseModel):
    """代码差异"""
    file_path: str = Field(..., description="文件路径")
    action: FileAction = Field(..., description="操作类型")
    old_content: Optional[str] = Field(None, description="原内容")
    new_content: Optional[str] = Field(None, description="新内容")
    diff: str = Field(default="", description="差异内容（unified diff 格式）")

    class Config:
        from_attributes = True


class MergeRequestInfo(BaseModel):
    """Merge Request 信息"""
    mr_id: str = Field(..., description="MR ID")
    title: str = Field(..., description="MR 标题")
    description: str = Field(default="", description="MR 描述")
    source_branch: str = Field(..., description="源分支")
    target_branch: str = Field(default="main", description="目标分支")
    url: Optional[str] = Field(None, description="MR 链接")
    status: str = Field(default="open", description="MR 状态")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class CodeGenTaskBase(BaseModel):
    """代码生成任务基础模型"""
    language: str = Field(default="python", description="主要编程语言")


class CodeGenTaskCreate(CodeGenTaskBase):
    """创建代码生成任务请求模型"""
    additional_context: Optional[str] = Field(None, description="额外上下文")


class CodeGenTask(BaseModel):
    """代码生成任务完整模型"""
    id: UUID = Field(default_factory=uuid4, description="任务 ID")
    solution_id: UUID = Field(..., description="关联方案 ID")
    requirement_id: UUID = Field(..., description="关联需求 ID")
    status: CodeGenStatus = Field(default=CodeGenStatus.PENDING, description="任务状态")
    language: str = Field(default="python", description="主要编程语言")
    files: List[CodeFile] = Field(default_factory=list, description="生成的文件列表")
    lint_result: Optional[LintResult] = Field(None, description="Lint 检查结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    sandbox_id: Optional[str] = Field(None, description="沙箱 ID")
    mr_info: Optional[MergeRequestInfo] = Field(None, description="MR 信息")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        from_attributes = True


class CodeGenTaskResponse(BaseModel):
    """代码生成任务列表响应模型"""
    items: List[CodeGenTask]
    total: int
    page: int = 1
    page_size: int = 20


class CodeGenRegenerateRequest(BaseModel):
    """重新生成代码请求模型"""
    files_to_regenerate: Optional[List[str]] = Field(
        None, description="指定要重新生成的文件路径，为空则全部重新生成"
    )
    fix_lint_errors: bool = Field(
        default=True, description="是否基于 lint 错误进行修复"
    )
    additional_instructions: Optional[str] = Field(
        None, description="额外指令"
    )


class CodeReviewSubmitRequest(BaseModel):
    """提交代码审核请求模型"""
    reviewer_notes: Optional[str] = Field(None, description="审核备注")
    auto_merge: bool = Field(default=False, description="是否自动合并")


class CodeGenFilters(BaseModel):
    """代码生成任务过滤条件"""
    status: Optional[CodeGenStatus] = None
    language: Optional[str] = None
    solution_id: Optional[UUID] = None


class SandboxInfo(BaseModel):
    """沙箱信息"""
    sandbox_id: str = Field(..., description="沙箱 ID")
    project_id: UUID = Field(..., description="项目 ID")
    status: str = Field(default="active", description="沙箱状态: active/destroyed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    working_directory: str = Field(default="/workspace", description="工作目录")

    class Config:
        from_attributes = True


class SandboxExecuteRequest(BaseModel):
    """沙箱执行命令请求"""
    command: str = Field(..., min_length=1, description="要执行的命令")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间（秒）")
    working_directory: Optional[str] = Field(None, description="工作目录")


class SandboxExecuteResult(BaseModel):
    """沙箱执行结果"""
    success: bool = Field(..., description="是否执行成功")
    exit_code: int = Field(..., description="退出码")
    stdout: str = Field(default="", description="标准输出")
    stderr: str = Field(default="", description="标准错误")
    duration_ms: int = Field(default=0, description="执行耗时（毫秒）")

    class Config:
        from_attributes = True


class FileWriteRequest(BaseModel):
    """写入文件请求"""
    path: str = Field(..., min_length=1, description="文件路径")
    content: str = Field(..., description="文件内容")
    create_dirs: bool = Field(default=True, description="是否自动创建目录")
