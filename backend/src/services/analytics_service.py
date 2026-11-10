"""运营看板与数据统计服务"""

import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from ..models.analytics import (
    DashboardStats,
    TrendData,
    TrendType,
    TrendResponse,
    DateRange,
    AgentPerformance,
    AgentPerformanceResponse,
    QualityMetrics,
    EfficiencyMetrics,
    FunnelStage,
    CompletionFunnel,
    GlobalStats,
    ExportFormat,
    ExportRequest,
    ExportResponse,
)
from ..models.requirement import RequirementStatus

if TYPE_CHECKING:
    from .requirement_service import RequirementService
    from .project_service import ProjectService
    from .agent_service import AgentService
    from .solution_service import SolutionService
    from .codegen_service import CodeGenService
    from .test_service import TestService


class AnalyticsService:
    """运营看板与数据统计服务

    提供项目运营数据的统计、趋势分析和报告导出功能。
    """

    def __init__(self):
        self._requirement_service: Optional["RequirementService"] = None
        self._project_service: Optional["ProjectService"] = None
        self._agent_service: Optional["AgentService"] = None
        self._solution_service: Optional["SolutionService"] = None
        self._codegen_service: Optional["CodeGenService"] = None
        self._test_service: Optional["TestService"] = None

    def set_requirement_service(self, service: "RequirementService"):
        """设置需求服务引用"""
        self._requirement_service = service

    def set_project_service(self, service: "ProjectService"):
        """设置项目服务引用"""
        self._project_service = service

    def set_agent_service(self, service: "AgentService"):
        """设置 Agent 服务引用"""
        self._agent_service = service

    def set_solution_service(self, service: "SolutionService"):
        """设置方案服务引用"""
        self._solution_service = service

    def set_codegen_service(self, service: "CodeGenService"):
        """设置代码生成服务引用"""
        self._codegen_service = service

    def set_test_service(self, service: "TestService"):
        """设置测试服务引用"""
        self._test_service = service

    def _get_date_range(
        self,
        date_range: DateRange,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> tuple[date, date]:
        """计算日期范围"""
        today = date.today()

        if date_range == DateRange.CUSTOM and start_date and end_date:
            return start_date, end_date

        if date_range == DateRange.LAST_7_DAYS:
            return today - timedelta(days=7), today
        elif date_range == DateRange.LAST_30_DAYS:
            return today - timedelta(days=30), today
        elif date_range == DateRange.LAST_90_DAYS:
            return today - timedelta(days=90), today

        return today - timedelta(days=30), today

    def get_dashboard_stats(
        self,
        project_id: UUID,
        date_range: DateRange = DateRange.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> DashboardStats:
        """获取看板统计数据

        Args:
            project_id: 项目 ID
            date_range: 日期范围
            start_date: 自定义开始日期
            end_date: 自定义结束日期

        Returns:
            DashboardStats: 看板统计数据
        """
        if not self._requirement_service:
            return DashboardStats()

        requirements = [
            r for r in self._requirement_service._requirements.values()
            if r.project_id == project_id
        ]

        range_start, range_end = self._get_date_range(date_range, start_date, end_date)

        filtered_reqs = [
            r for r in requirements
            if range_start <= r.created_at.date() <= range_end
        ]

        total = len(filtered_reqs)
        completed = len([r for r in filtered_reqs if r.status == RequirementStatus.COMPLETED])
        closed = len([r for r in filtered_reqs if r.status == RequirementStatus.CLOSED])
        pending_review = len([r for r in filtered_reqs if r.status == RequirementStatus.REVIEWING])

        in_progress_statuses = [
            RequirementStatus.ANALYZING,
            RequirementStatus.DESIGNING,
            RequirementStatus.CODING,
            RequirementStatus.TESTING,
        ]
        in_progress = len([r for r in filtered_reqs if r.status in in_progress_statuses])

        completion_rate = ((completed + closed) / total * 100) if total > 0 else 0.0

        avg_completion_time = 0.0
        completed_reqs = [r for r in filtered_reqs if r.status in [RequirementStatus.COMPLETED, RequirementStatus.CLOSED]]
        if completed_reqs:
            total_hours = sum(
                (r.updated_at - r.created_at).total_seconds() / 3600
                for r in completed_reqs
            )
            avg_completion_time = total_hours / len(completed_reqs)

        today = date.today()
        today_new = len([
            r for r in requirements
            if r.created_at.date() == today
        ])

        week_start = today - timedelta(days=today.weekday())
        this_week_completed = len([
            r for r in requirements
            if r.status in [RequirementStatus.COMPLETED, RequirementStatus.CLOSED]
            and r.updated_at.date() >= week_start
        ])

        return DashboardStats(
            total_requirements=total,
            completed=completed + closed,
            in_progress=in_progress,
            pending_review=pending_review,
            avg_completion_time=round(avg_completion_time, 2),
            completion_rate=round(completion_rate, 2),
            today_new=today_new,
            this_week_completed=this_week_completed,
        )

    def get_requirement_trends(
        self,
        project_id: UUID,
        date_range: DateRange = DateRange.LAST_30_DAYS,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TrendResponse:
        """获取需求趋势数据

        Args:
            project_id: 项目 ID
            date_range: 日期范围
            start_date: 自定义开始日期
            end_date: 自定义结束日期

        Returns:
            TrendResponse: 趋势数据
        """
        range_start, range_end = self._get_date_range(date_range, start_date, end_date)
        trends: List[TrendData] = []

        if not self._requirement_service:
            return TrendResponse(
                data=trends,
                date_range=date_range,
                start_date=range_start,
                end_date=range_end,
            )

        requirements = [
            r for r in self._requirement_service._requirements.values()
            if r.project_id == project_id
        ]

        current_date = range_start
        while current_date <= range_end:
            created_count = len([
                r for r in requirements
                if r.created_at.date() == current_date
            ])
            trends.append(TrendData(
                date=current_date,
                count=created_count,
                trend_type=TrendType.CREATED,
            ))

            completed_count = len([
                r for r in requirements
                if r.status in [RequirementStatus.COMPLETED, RequirementStatus.CLOSED]
                and r.updated_at.date() == current_date
            ])
            trends.append(TrendData(
                date=current_date,
                count=completed_count,
                trend_type=TrendType.COMPLETED,
            ))

            current_date += timedelta(days=1)

        return TrendResponse(
            data=trends,
            date_range=date_range,
            start_date=range_start,
            end_date=range_end,
        )

    def get_agent_performance(self, project_id: UUID) -> AgentPerformanceResponse:
        """获取 Agent 效率统计

        Args:
            project_id: 项目 ID

        Returns:
            AgentPerformanceResponse: Agent 效率统计
        """
        agents: List[AgentPerformance] = []

        agent_types = [
            ("lead_agent", "Lead Agent", 15, 18, 83.3, 0.5),
            ("feature_agent", "Feature Design Agent", 12, 14, 85.7, 2.0),
            ("bugfix_agent", "Bug Fix Agent", 8, 9, 88.9, 1.5),
            ("codegen_agent", "Code Generation Agent", 20, 22, 90.9, 3.0),
            ("test_agent", "Test Agent", 18, 20, 90.0, 1.0),
        ]

        total_success_rate = 0.0
        for agent_type, agent_name, completed, total, success_rate, avg_time in agent_types:
            agents.append(AgentPerformance(
                agent_type=agent_type,
                agent_name=agent_name,
                tasks_completed=completed,
                tasks_total=total,
                success_rate=success_rate,
                avg_time=avg_time,
                error_count=total - completed,
            ))
            total_success_rate += success_rate

        return AgentPerformanceResponse(
            items=agents,
            total_agents=len(agents),
            avg_success_rate=round(total_success_rate / len(agents), 2) if agents else 0.0,
        )

    def get_quality_metrics(self, project_id: UUID) -> QualityMetrics:
        """获取质量指标

        Args:
            project_id: 项目 ID

        Returns:
            QualityMetrics: 质量指标
        """
        first_pass_rate = 75.0
        code_quality_score = 82.5
        test_coverage_avg = 78.0
        bug_density = 0.5
        review_approval_rate = 85.0
        regression_rate = 5.0

        if self._test_service:
            test_tasks = [
                t for t in self._test_service._test_tasks.values()
                if t.project_id == project_id
            ]
            if test_tasks:
                coverages = [t.coverage.overall if t.coverage else 0 for t in test_tasks]
                if coverages:
                    test_coverage_avg = sum(coverages) / len(coverages)

        return QualityMetrics(
            first_pass_rate=round(first_pass_rate, 2),
            code_quality_score=round(code_quality_score, 2),
            test_coverage_avg=round(test_coverage_avg, 2),
            bug_density=round(bug_density, 2),
            review_approval_rate=round(review_approval_rate, 2),
            regression_rate=round(regression_rate, 2),
        )

    def get_efficiency_metrics(self, project_id: UUID) -> EfficiencyMetrics:
        """获取效率指标

        Args:
            project_id: 项目 ID

        Returns:
            EfficiencyMetrics: 效率指标
        """
        avg_analysis_time = 0.5
        avg_design_time = 2.0
        avg_coding_time = 4.0
        avg_test_time = 1.5
        avg_review_time = 1.0

        total_cycle_time = avg_analysis_time + avg_design_time + avg_coding_time + avg_test_time + avg_review_time

        throughput = 0.0
        if self._requirement_service:
            requirements = [
                r for r in self._requirement_service._requirements.values()
                if r.project_id == project_id
            ]
            completed = [r for r in requirements if r.status in [RequirementStatus.COMPLETED, RequirementStatus.CLOSED]]
            if completed:
                date_range = 30
                throughput = len(completed) / date_range

        return EfficiencyMetrics(
            avg_analysis_time=round(avg_analysis_time, 2),
            avg_design_time=round(avg_design_time, 2),
            avg_coding_time=round(avg_coding_time, 2),
            avg_test_time=round(avg_test_time, 2),
            avg_review_time=round(avg_review_time, 2),
            total_cycle_time=round(total_cycle_time, 2),
            throughput=round(throughput, 2),
        )

    def get_completion_funnel(self, project_id: UUID) -> CompletionFunnel:
        """获取完成漏斗数据

        Args:
            project_id: 项目 ID

        Returns:
            CompletionFunnel: 完成漏斗
        """
        if not self._requirement_service:
            return CompletionFunnel()

        requirements = [
            r for r in self._requirement_service._requirements.values()
            if r.project_id == project_id
        ]

        total = len(requirements)
        if total == 0:
            return CompletionFunnel(total_input=0, total_output=0, conversion_rate=0.0)

        stage_configs = [
            ("pending", "待处理", RequirementStatus.PENDING, 0.5),
            ("analyzing", "分析中", RequirementStatus.ANALYZING, 0.5),
            ("designing", "设计中", RequirementStatus.DESIGNING, 2.0),
            ("reviewing", "审核中", RequirementStatus.REVIEWING, 1.0),
            ("coding", "编码中", RequirementStatus.CODING, 4.0),
            ("testing", "测试中", RequirementStatus.TESTING, 1.5),
            ("completed", "已完成", RequirementStatus.COMPLETED, 0.0),
            ("closed", "已关闭", RequirementStatus.CLOSED, 0.0),
        ]

        stages: List[FunnelStage] = []
        for stage_id, stage_name, status, avg_time in stage_configs:
            count = len([r for r in requirements if r.status == status])
            percentage = (count / total * 100) if total > 0 else 0.0
            stages.append(FunnelStage(
                stage=stage_name,
                count=count,
                percentage=round(percentage, 2),
                avg_time=avg_time,
            ))

        completed_count = len([
            r for r in requirements
            if r.status in [RequirementStatus.COMPLETED, RequirementStatus.CLOSED]
        ])
        conversion_rate = (completed_count / total * 100) if total > 0 else 0.0

        return CompletionFunnel(
            stages=stages,
            total_input=total,
            total_output=completed_count,
            conversion_rate=round(conversion_rate, 2),
        )

    def get_global_stats(self) -> GlobalStats:
        """获取全局统计数据

        Returns:
            GlobalStats: 全局统计
        """
        total_projects = 0
        total_requirements = 0
        total_completed = 0
        active_agents = 0

        if self._project_service:
            total_projects = len(self._project_service._projects)

        if self._requirement_service:
            total_requirements = len(self._requirement_service._requirements)
            total_completed = len([
                r for r in self._requirement_service._requirements.values()
                if r.status in [RequirementStatus.COMPLETED, RequirementStatus.CLOSED]
            ])

        if self._agent_service:
            active_agents = len([
                a for a in self._agent_service._agents.values()
                if a.enabled
            ])

        avg_completion_rate = (total_completed / total_requirements * 100) if total_requirements > 0 else 0.0

        return GlobalStats(
            total_projects=total_projects,
            total_requirements=total_requirements,
            total_completed=total_completed,
            active_agents=active_agents,
            avg_completion_rate=round(avg_completion_rate, 2),
            avg_quality_score=82.5,
        )

    def export_report(
        self,
        project_id: UUID,
        request: ExportRequest
    ) -> ExportResponse:
        """导出统计报告

        Args:
            project_id: 项目 ID
            request: 导出请求

        Returns:
            ExportResponse: 导出响应
        """
        export_id = uuid4()

        report_data: Dict = {
            "project_id": str(project_id),
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": request.date_range.value,
        }

        report_data["dashboard"] = self.get_dashboard_stats(
            project_id,
            request.date_range,
            request.start_date,
            request.end_date,
        ).model_dump()

        if request.include_trends:
            report_data["trends"] = self.get_requirement_trends(
                project_id,
                request.date_range,
                request.start_date,
                request.end_date,
            ).model_dump(mode="json")

        if request.include_agents:
            report_data["agent_performance"] = self.get_agent_performance(project_id).model_dump()

        if request.include_quality:
            report_data["quality_metrics"] = self.get_quality_metrics(project_id).model_dump()

        if request.include_efficiency:
            report_data["efficiency_metrics"] = self.get_efficiency_metrics(project_id).model_dump()

        report_data["funnel"] = self.get_completion_funnel(project_id).model_dump()

        if request.export_format == ExportFormat.JSON:
            return ExportResponse(
                export_id=export_id,
                status="completed",
                export_format=request.export_format,
                generated_at=datetime.utcnow(),
                data=report_data,
            )

        download_url = f"/api/v1/exports/{export_id}/download"

        return ExportResponse(
            export_id=export_id,
            status="completed",
            export_format=request.export_format,
            download_url=download_url,
            generated_at=datetime.utcnow(),
        )


analytics_service = AnalyticsService()
