"""运营看板与数据统计模型定义"""

from datetime import date as DateType, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TrendType(str, Enum):
    """趋势数据类型"""
    CREATED = "created"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


class DateRange(str, Enum):
    """日期范围"""
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    """导出格式"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class DashboardStats(BaseModel):
    """看板统计数据"""
    total_requirements: int = Field(default=0, description="总需求数")
    completed: int = Field(default=0, description="已完成数")
    in_progress: int = Field(default=0, description="进行中数")
    pending_review: int = Field(default=0, description="待审核数")
    avg_completion_time: float = Field(default=0.0, description="平均完成时间（小时）")
    completion_rate: float = Field(default=0.0, description="完成率")
    today_new: int = Field(default=0, description="今日新增")
    this_week_completed: int = Field(default=0, description="本周完成")


class TrendData(BaseModel):
    """趋势数据点"""
    date: DateType = Field(..., description="日期")
    count: int = Field(default=0, description="数量")
    trend_type: TrendType = Field(..., description="趋势类型")


class TrendResponse(BaseModel):
    """趋势数据响应"""
    data: List[TrendData] = Field(default_factory=list, description="趋势数据列表")
    date_range: DateRange = Field(..., description="日期范围")
    start_date: DateType = Field(..., description="开始日期")
    end_date: DateType = Field(..., description="结束日期")


class AgentPerformance(BaseModel):
    """Agent 效率统计"""
    agent_type: str = Field(..., description="Agent 类型")
    agent_name: str = Field(..., description="Agent 名称")
    tasks_completed: int = Field(default=0, description="完成任务数")
    tasks_total: int = Field(default=0, description="总任务数")
    success_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="成功率（%）")
    avg_time: float = Field(default=0.0, description="平均处理时间（小时）")
    error_count: int = Field(default=0, description="错误次数")


class AgentPerformanceResponse(BaseModel):
    """Agent 效率统计响应"""
    items: List[AgentPerformance] = Field(default_factory=list, description="Agent 效率列表")
    total_agents: int = Field(default=0, description="Agent 总数")
    avg_success_rate: float = Field(default=0.0, description="平均成功率")


class QualityMetrics(BaseModel):
    """质量指标"""
    first_pass_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="一次通过率（%）")
    code_quality_score: float = Field(default=0.0, ge=0.0, le=100.0, description="代码质量评分")
    test_coverage_avg: float = Field(default=0.0, ge=0.0, le=100.0, description="平均测试覆盖率（%）")
    bug_density: float = Field(default=0.0, description="缺陷密度（每千行代码）")
    review_approval_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="审核通过率（%）")
    regression_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="回归率（%）")


class EfficiencyMetrics(BaseModel):
    """效率指标"""
    avg_analysis_time: float = Field(default=0.0, description="平均分析时间（小时）")
    avg_design_time: float = Field(default=0.0, description="平均设计时间（小时）")
    avg_coding_time: float = Field(default=0.0, description="平均编码时间（小时）")
    avg_test_time: float = Field(default=0.0, description="平均测试时间（小时）")
    avg_review_time: float = Field(default=0.0, description="平均审核时间（小时）")
    total_cycle_time: float = Field(default=0.0, description="总周期时间（小时）")
    throughput: float = Field(default=0.0, description="吞吐量（需求/天）")


class FunnelStage(BaseModel):
    """漏斗阶段"""
    stage: str = Field(..., description="阶段名称")
    count: int = Field(default=0, description="数量")
    percentage: float = Field(default=0.0, description="占比（%）")
    avg_time: float = Field(default=0.0, description="平均停留时间（小时）")


class CompletionFunnel(BaseModel):
    """完成漏斗数据"""
    stages: List[FunnelStage] = Field(default_factory=list, description="漏斗阶段列表")
    total_input: int = Field(default=0, description="漏斗入口总数")
    total_output: int = Field(default=0, description="漏斗出口总数")
    conversion_rate: float = Field(default=0.0, description="转化率（%）")


class GlobalStats(BaseModel):
    """全局统计数据"""
    total_projects: int = Field(default=0, description="项目总数")
    total_requirements: int = Field(default=0, description="需求总数")
    total_completed: int = Field(default=0, description="完成总数")
    active_agents: int = Field(default=0, description="活跃 Agent 数")
    avg_completion_rate: float = Field(default=0.0, description="平均完成率")
    avg_quality_score: float = Field(default=0.0, description="平均质量评分")


class ExportRequest(BaseModel):
    """导出报告请求"""
    export_format: ExportFormat = Field(default=ExportFormat.JSON, description="导出格式")
    date_range: DateRange = Field(default=DateRange.LAST_30_DAYS, description="日期范围")
    start_date: Optional[DateType] = Field(None, description="自定义开始日期")
    end_date: Optional[DateType] = Field(None, description="自定义结束日期")
    include_trends: bool = Field(default=True, description="包含趋势数据")
    include_agents: bool = Field(default=True, description="包含 Agent 统计")
    include_quality: bool = Field(default=True, description="包含质量指标")
    include_efficiency: bool = Field(default=True, description="包含效率指标")


class ExportResponse(BaseModel):
    """导出报告响应"""
    export_id: UUID = Field(..., description="导出任务 ID")
    status: str = Field(default="completed", description="导出状态")
    export_format: ExportFormat = Field(..., description="导出格式")
    download_url: Optional[str] = Field(None, description="下载链接")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")
    data: Optional[dict] = Field(None, description="JSON 格式的导出数据")


class AnalyticsFilters(BaseModel):
    """统计过滤条件"""
    date_range: DateRange = Field(default=DateRange.LAST_30_DAYS, description="日期范围")
    start_date: Optional[DateType] = Field(None, description="自定义开始日期")
    end_date: Optional[DateType] = Field(None, description="自定义结束日期")
