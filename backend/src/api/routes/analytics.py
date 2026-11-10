"""运营看板与数据统计 API"""

from typing import Optional
from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...models.analytics import (
    DashboardStats,
    TrendResponse,
    DateRange,
    AgentPerformanceResponse,
    QualityMetrics,
    EfficiencyMetrics,
    CompletionFunnel,
    GlobalStats,
    ExportRequest,
    ExportResponse,
)
from ...services.analytics_service import analytics_service
from ...services.project_service import project_service

router = APIRouter()


@router.get("/projects/{project_id}/analytics/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    project_id: UUID,
    date_range: DateRange = Query(DateRange.LAST_30_DAYS, description="日期范围"),
    start_date: Optional[date] = Query(None, description="自定义开始日期（需配合 date_range=custom）"),
    end_date: Optional[date] = Query(None, description="自定义结束日期（需配合 date_range=custom）"),
) -> DashboardStats:
    """
    获取项目看板统计数据

    返回项目的核心运营指标：
    - **total_requirements**: 总需求数
    - **completed**: 已完成数
    - **in_progress**: 进行中数
    - **pending_review**: 待审核数
    - **avg_completion_time**: 平均完成时间（小时）
    - **completion_rate**: 完成率（%）
    - **today_new**: 今日新增
    - **this_week_completed**: 本周完成
    """
    proj = project_service.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return analytics_service.get_dashboard_stats(
        project_id,
        date_range,
        start_date,
        end_date,
    )


@router.get("/projects/{project_id}/analytics/trends", response_model=TrendResponse)
async def get_requirement_trends(
    project_id: UUID,
    date_range: DateRange = Query(DateRange.LAST_30_DAYS, description="日期范围"),
    start_date: Optional[date] = Query(None, description="自定义开始日期"),
    end_date: Optional[date] = Query(None, description="自定义结束日期"),
) -> TrendResponse:
    """
    获取需求趋势数据

    返回指定时间范围内的需求创建和完成趋势：
    - 每日创建数量
    - 每日完成数量

    支持的日期范围：
    - **7d**: 最近 7 天
    - **30d**: 最近 30 天
    - **90d**: 最近 90 天
    - **custom**: 自定义范围（需提供 start_date 和 end_date）
    """
    proj = project_service.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return analytics_service.get_requirement_trends(
        project_id,
        date_range,
        start_date,
        end_date,
    )


@router.get("/projects/{project_id}/analytics/agents", response_model=AgentPerformanceResponse)
async def get_agent_performance(project_id: UUID) -> AgentPerformanceResponse:
    """
    获取 Agent 效率统计

    返回项目中各个 Agent 的性能指标：
    - **agent_type**: Agent 类型
    - **tasks_completed**: 完成任务数
    - **success_rate**: 成功率
    - **avg_time**: 平均处理时间
    - **error_count**: 错误次数
    """
    proj = project_service.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return analytics_service.get_agent_performance(project_id)


@router.get("/projects/{project_id}/analytics/quality", response_model=QualityMetrics)
async def get_quality_metrics(project_id: UUID) -> QualityMetrics:
    """
    获取质量指标

    返回项目的代码和交付质量指标：
    - **first_pass_rate**: 一次通过率
    - **code_quality_score**: 代码质量评分
    - **test_coverage_avg**: 平均测试覆盖率
    - **bug_density**: 缺陷密度
    - **review_approval_rate**: 审核通过率
    - **regression_rate**: 回归率
    """
    proj = project_service.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return analytics_service.get_quality_metrics(project_id)


@router.get("/projects/{project_id}/analytics/efficiency", response_model=EfficiencyMetrics)
async def get_efficiency_metrics(project_id: UUID) -> EfficiencyMetrics:
    """
    获取效率指标

    返回需求处理流程各阶段的时间消耗：
    - **avg_analysis_time**: 平均分析时间
    - **avg_design_time**: 平均设计时间
    - **avg_coding_time**: 平均编码时间
    - **avg_test_time**: 平均测试时间
    - **avg_review_time**: 平均审核时间
    - **total_cycle_time**: 总周期时间
    - **throughput**: 吞吐量（需求/天）
    """
    proj = project_service.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return analytics_service.get_efficiency_metrics(project_id)


@router.get("/projects/{project_id}/analytics/funnel", response_model=CompletionFunnel)
async def get_completion_funnel(project_id: UUID) -> CompletionFunnel:
    """
    获取完成漏斗数据

    返回需求从创建到完成的各阶段漏斗数据：
    - 各阶段的需求数量和占比
    - 各阶段的平均停留时间
    - 整体转化率
    """
    proj = project_service.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return analytics_service.get_completion_funnel(project_id)


@router.get("/analytics/global", response_model=GlobalStats)
async def get_global_stats() -> GlobalStats:
    """
    获取全局统计数据

    返回系统级别的整体运营数据：
    - **total_projects**: 项目总数
    - **total_requirements**: 需求总数
    - **total_completed**: 完成总数
    - **active_agents**: 活跃 Agent 数
    - **avg_completion_rate**: 平均完成率
    - **avg_quality_score**: 平均质量评分
    """
    return analytics_service.get_global_stats()


@router.post("/projects/{project_id}/analytics/export", response_model=ExportResponse)
async def export_analytics_report(
    project_id: UUID,
    request: ExportRequest
) -> ExportResponse:
    """
    导出统计报告

    生成并导出项目的统计报告，支持多种格式：
    - **json**: JSON 格式（直接返回数据）
    - **csv**: CSV 格式
    - **pdf**: PDF 格式

    可选择包含的内容：
    - **include_trends**: 趋势数据
    - **include_agents**: Agent 统计
    - **include_quality**: 质量指标
    - **include_efficiency**: 效率指标
    """
    proj = project_service.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return analytics_service.export_report(project_id, request)
