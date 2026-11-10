"""方案模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SolutionType(str, Enum):
    """方案类型"""
    BUGFIX = "bugfix"
    FEATURE_DESIGN = "feature_design"


class SolutionStatus(str, Enum):
    """方案状态"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class ImpactLevel(str, Enum):
    """影响级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImpactAnalysis(BaseModel):
    """影响分析"""
    level: ImpactLevel = Field(default=ImpactLevel.MEDIUM, description="影响级别")
    scope: str = Field(default="", description="影响范围")
    affected_modules: List[str] = Field(default_factory=list, description="受影响模块")
    affected_services: List[str] = Field(default_factory=list, description="受影响服务")
    risk_points: List[str] = Field(default_factory=list, description="风险点")
    mitigation_strategies: List[str] = Field(default_factory=list, description="缓解策略")


class SolutionBase(BaseModel):
    """方案基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="方案标题")
    content: str = Field(..., min_length=1, max_length=50000, description="方案内容")


class SolutionCreate(SolutionBase):
    """创建方案请求模型"""
    type: SolutionType = Field(..., description="方案类型")
    impact_analysis: Optional[ImpactAnalysis] = Field(None, description="影响分析")
    affected_files: List[str] = Field(default_factory=list, description="受影响文件")


class SolutionUpdate(BaseModel):
    """更新方案请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="方案标题")
    content: Optional[str] = Field(None, min_length=1, max_length=50000, description="方案内容")
    impact_analysis: Optional[ImpactAnalysis] = Field(None, description="影响分析")
    affected_files: Optional[List[str]] = Field(None, description="受影响文件")


class SolutionStatusUpdate(BaseModel):
    """更新方案状态请求模型"""
    status: SolutionStatus = Field(..., description="新状态")
    review_comment: Optional[str] = Field(None, max_length=2000, description="审核意见")


class Solution(SolutionBase):
    """方案完整模型"""
    id: UUID = Field(default_factory=uuid4, description="方案 ID")
    requirement_id: UUID = Field(..., description="关联需求 ID")
    type: SolutionType = Field(..., description="方案类型")
    impact_analysis: ImpactAnalysis = Field(
        default_factory=ImpactAnalysis, description="影响分析"
    )
    affected_files: List[str] = Field(default_factory=list, description="受影响文件")
    status: SolutionStatus = Field(default=SolutionStatus.DRAFT, description="方案状态")
    created_by_agent: str = Field(default="", description="创建方案的 Agent")
    reviewed_by: Optional[str] = Field(None, description="审核人")
    review_comment: Optional[str] = Field(None, description="审核意见")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        from_attributes = True


class BugFixSolution(Solution):
    """Bug 修复方案"""
    root_cause: str = Field(default="", description="根因分析")
    fix_steps: List[str] = Field(default_factory=list, description="修复步骤")
    regression_risk: str = Field(default="", description="回归风险评估")
    test_cases: List[str] = Field(default_factory=list, description="测试用例建议")
    rollback_plan: str = Field(default="", description="回滚方案")


class APIEndpoint(BaseModel):
    """API 端点设计"""
    method: str = Field(..., description="HTTP 方法")
    path: str = Field(..., description="请求路径")
    description: str = Field(default="", description="接口描述")
    request_body: Optional[Dict[str, Any]] = Field(None, description="请求体结构")
    response_body: Optional[Dict[str, Any]] = Field(None, description="响应体结构")


class DatabaseChange(BaseModel):
    """数据库变更"""
    change_type: str = Field(..., description="变更类型: create_table/alter_table/create_index 等")
    table_name: str = Field(..., description="表名")
    description: str = Field(default="", description="变更描述")
    sql_migration: Optional[str] = Field(None, description="SQL 迁移脚本")


class ArchitectureComponent(BaseModel):
    """架构组件"""
    name: str = Field(..., description="组件名称")
    type: str = Field(..., description="组件类型")
    description: str = Field(default="", description="组件描述")
    dependencies: List[str] = Field(default_factory=list, description="依赖")
    interfaces: List[str] = Field(default_factory=list, description="接口")


class FeatureDesignSolution(Solution):
    """功能设计方案"""
    architecture: List[ArchitectureComponent] = Field(
        default_factory=list, description="架构设计"
    )
    api_design: List[APIEndpoint] = Field(default_factory=list, description="API 设计")
    database_changes: List[DatabaseChange] = Field(
        default_factory=list, description="数据库变更"
    )
    dependencies: List[str] = Field(default_factory=list, description="依赖项")
    implementation_phases: List[str] = Field(
        default_factory=list, description="实现阶段"
    )
    non_functional_requirements: Dict[str, str] = Field(
        default_factory=dict, description="非功能需求"
    )


class SolutionResponse(BaseModel):
    """方案列表响应模型"""
    items: List[Solution]
    total: int
    page: int = 1
    page_size: int = 20


class SolutionGenerateRequest(BaseModel):
    """生成方案请求模型"""
    force_regenerate: bool = Field(default=False, description="强制重新生成")
    additional_context: Optional[str] = Field(None, description="额外上下文信息")


class SolutionFilters(BaseModel):
    """方案过滤条件"""
    type: Optional[SolutionType] = None
    status: Optional[SolutionStatus] = None
    created_by_agent: Optional[str] = None
