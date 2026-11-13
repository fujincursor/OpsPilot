"""测试模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """测试任务状态"""
    PENDING = "pending"
    GENERATING = "generating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestCaseType(str, Enum):
    """测试用例类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"


class TestResultStatus(str, Enum):
    """测试结果状态"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestCase(BaseModel):
    """测试用例模型"""
    id: UUID = Field(default_factory=uuid4, description="测试用例 ID")
    name: str = Field(..., min_length=1, max_length=200, description="用例名称")
    description: str = Field(default="", description="用例描述")
    type: TestCaseType = Field(default=TestCaseType.UNIT, description="用例类型")
    code: str = Field(default="", description="测试代码")
    expected_result: Optional[str] = Field(None, description="预期结果")
    file_path: str = Field(default="", description="测试文件路径")
    target_function: Optional[str] = Field(None, description="目标函数/方法")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class TestResult(BaseModel):
    """测试结果模型"""
    test_case_id: UUID = Field(..., description="测试用例 ID")
    status: TestResultStatus = Field(..., description="执行状态")
    actual_result: Optional[str] = Field(None, description="实际结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    duration_ms: int = Field(default=0, description="执行耗时（毫秒）")
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="执行时间")

    class Config:
        from_attributes = True


class CoverageInfo(BaseModel):
    """代码覆盖率信息"""
    lines_total: int = Field(default=0, description="总行数")
    lines_covered: int = Field(default=0, description="覆盖行数")
    lines_percent: float = Field(default=0.0, description="行覆盖率")
    branches_total: int = Field(default=0, description="总分支数")
    branches_covered: int = Field(default=0, description="覆盖分支数")
    branches_percent: float = Field(default=0.0, description="分支覆盖率")
    functions_total: int = Field(default=0, description="总函数数")
    functions_covered: int = Field(default=0, description="覆盖函数数")
    functions_percent: float = Field(default=0.0, description="函数覆盖率")
    files: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="文件级覆盖率")

    class Config:
        from_attributes = True


class TestReport(BaseModel):
    """测试报告模型"""
    task_id: UUID = Field(..., description="测试任务 ID")
    total: int = Field(default=0, description="用例总数")
    passed: int = Field(default=0, description="通过数量")
    failed: int = Field(default=0, description="失败数量")
    skipped: int = Field(default=0, description="跳过数量")
    coverage_percent: float = Field(default=0.0, description="代码覆盖率")
    coverage_info: Optional[CoverageInfo] = Field(None, description="详细覆盖率信息")
    duration_ms: int = Field(default=0, description="总执行耗时（毫秒）")
    failed_cases: List[str] = Field(default_factory=list, description="失败用例名称列表")
    summary: str = Field(default="", description="报告摘要")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")

    class Config:
        from_attributes = True


class TestTask(BaseModel):
    """测试任务模型"""
    id: UUID = Field(default_factory=uuid4, description="任务 ID")
    codegen_task_id: UUID = Field(..., description="关联代码生成任务 ID")
    requirement_id: UUID = Field(..., description="关联需求 ID")
    status: TestStatus = Field(default=TestStatus.PENDING, description="任务状态")
    test_cases: List[TestCase] = Field(default_factory=list, description="测试用例列表")
    results: List[TestResult] = Field(default_factory=list, description="测试结果列表")
    coverage: Optional[CoverageInfo] = Field(None, description="覆盖率信息")
    error_message: Optional[str] = Field(None, description="错误信息")
    sandbox_id: Optional[str] = Field(None, description="沙箱 ID")
    sandbox_profile: Optional[str] = Field(None, description="执行时使用的沙箱配置摘要")
    ci_pipeline_id: Optional[str] = Field(None, description="CI 流水线 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        from_attributes = True


class TestTaskCreate(BaseModel):
    """创建测试任务请求模型"""
    additional_context: Optional[str] = Field(None, description="额外上下文")
    test_types: List[TestCaseType] = Field(
        default=[TestCaseType.UNIT],
        description="要生成的测试类型"
    )


class TestTaskResponse(BaseModel):
    """测试任务列表响应模型"""
    items: List[TestTask]
    total: int
    page: int = 1
    page_size: int = 20


class TestRerunRequest(BaseModel):
    """重新运行测试请求模型"""
    test_case_ids: Optional[List[UUID]] = Field(
        None, description="指定要重新运行的测试用例 ID，为空则全部重新运行"
    )
    fix_failed_tests: bool = Field(
        default=False, description="是否尝试修复失败的测试"
    )


class TestReviewSubmitRequest(BaseModel):
    """提交测试审核请求模型"""
    reviewer_notes: Optional[str] = Field(None, description="审核备注")
    approve_with_failures: bool = Field(
        default=False, description="是否允许带失败用例提交"
    )


class CITriggerRequest(BaseModel):
    """触发 CI 请求模型"""
    target_branch: str = Field(default="main", description="目标分支")
    run_full_suite: bool = Field(default=False, description="是否运行完整测试套件")
    extra_args: Optional[Dict[str, str]] = Field(None, description="额外参数")


class CIPipelineInfo(BaseModel):
    """CI 流水线信息"""
    pipeline_id: str = Field(..., description="流水线 ID")
    status: str = Field(default="pending", description="流水线状态")
    url: Optional[str] = Field(None, description="流水线链接")
    triggered_at: datetime = Field(default_factory=datetime.utcnow, description="触发时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    stages: List[Dict[str, Any]] = Field(default_factory=list, description="阶段列表")

    class Config:
        from_attributes = True


class TestFilters(BaseModel):
    """测试任务过滤条件"""
    status: Optional[TestStatus] = None
    codegen_task_id: Optional[UUID] = None
    requirement_id: Optional[UUID] = None
