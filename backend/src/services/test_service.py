"""测试服务

负责测试任务的管理和协调，包括：
- 创建和管理测试任务
- 调用 TestAgent 生成和执行测试
- 生成测试报告
- 触发 CI 流水线
"""

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from ..models.test import (
    TestTask,
    TestTaskCreate,
    TestStatus,
    TestCase,
    TestCaseType,
    TestResult,
    TestResultStatus,
    TestReport,
    CoverageInfo,
    TestFilters,
    CIPipelineInfo,
)
from ..models.codegen import CodeGenTask, CodeGenStatus
from .agents.test_agent import test_agent_service
from .sandbox_service import sandbox_service

if TYPE_CHECKING:
    from .codegen_service import CodeGenService
    from .requirement_service import RequirementService


class TestService:
    """测试服务

    负责协调测试的完整流程：
    1. 创建测试任务
    2. 调用 TestAgent 生成测试用例
    3. 执行测试
    4. 生成测试报告
    5. 触发 CI 流水线
    """

    def __init__(self):
        self._tasks: Dict[UUID, TestTask] = {}
        self._codegen_to_tests: Dict[UUID, List[UUID]] = {}
        self._reports: Dict[UUID, TestReport] = {}
        self._ci_pipelines: Dict[UUID, CIPipelineInfo] = {}
        self._codegen_service: Optional["CodeGenService"] = None
        self._requirement_service: Optional["RequirementService"] = None

    def set_codegen_service(self, codegen_service: "CodeGenService"):
        """设置代码生成服务引用"""
        self._codegen_service = codegen_service

    def set_requirement_service(self, requirement_service: "RequirementService"):
        """设置需求服务引用"""
        self._requirement_service = requirement_service

    def create_test_task(
        self,
        codegen_task_id: UUID,
        data: Optional[TestTaskCreate] = None,
    ) -> Optional[TestTask]:
        """创建测试任务

        Args:
            codegen_task_id: 代码生成任务 ID
            data: 创建选项

        Returns:
            TestTask: 创建的任务，代码生成任务不存在返回 None
        """
        if not self._codegen_service:
            raise RuntimeError("CodeGenService not set")

        codegen_task = self._codegen_service.get_task(codegen_task_id)
        if not codegen_task:
            return None

        if codegen_task.status != CodeGenStatus.COMPLETED:
            return None

        task = TestTask(
            codegen_task_id=codegen_task_id,
            requirement_id=codegen_task.requirement_id,
            status=TestStatus.PENDING,
        )

        self._tasks[task.id] = task

        if codegen_task_id not in self._codegen_to_tests:
            self._codegen_to_tests[codegen_task_id] = []
        self._codegen_to_tests[codegen_task_id].append(task.id)

        return task

    def get_task(self, task_id: UUID) -> Optional[TestTask]:
        """获取测试任务

        Args:
            task_id: 任务 ID

        Returns:
            TestTask: 任务对象，不存在返回 None
        """
        return self._tasks.get(task_id)

    def get_tasks_by_codegen(
        self,
        codegen_task_id: UUID,
        filters: Optional[TestFilters] = None,
    ) -> List[TestTask]:
        """获取代码生成任务的测试任务列表

        Args:
            codegen_task_id: 代码生成任务 ID
            filters: 过滤条件

        Returns:
            List[TestTask]: 任务列表
        """
        task_ids = self._codegen_to_tests.get(codegen_task_id, [])
        tasks = [self._tasks[tid] for tid in task_ids if tid in self._tasks]

        if filters:
            if filters.status:
                tasks = [t for t in tasks if t.status == filters.status]
            if filters.requirement_id:
                tasks = [t for t in tasks if t.requirement_id == filters.requirement_id]

        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    def list_tasks(
        self,
        filters: Optional[TestFilters] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[TestTask]:
        """列出测试任务

        Args:
            filters: 过滤条件
            page: 页码
            page_size: 每页数量

        Returns:
            List[TestTask]: 任务列表
        """
        tasks = list(self._tasks.values())

        if filters:
            if filters.status:
                tasks = [t for t in tasks if t.status == filters.status]
            if filters.codegen_task_id:
                tasks = [t for t in tasks if t.codegen_task_id == filters.codegen_task_id]
            if filters.requirement_id:
                tasks = [t for t in tasks if t.requirement_id == filters.requirement_id]

        tasks.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return tasks[start:end]

    def count_tasks(self, filters: Optional[TestFilters] = None) -> int:
        """统计测试任务数量"""
        if not filters:
            return len(self._tasks)

        tasks = list(self._tasks.values())
        if filters.status:
            tasks = [t for t in tasks if t.status == filters.status]
        if filters.codegen_task_id:
            tasks = [t for t in tasks if t.codegen_task_id == filters.codegen_task_id]
        if filters.requirement_id:
            tasks = [t for t in tasks if t.requirement_id == filters.requirement_id]

        return len(tasks)

    async def generate_and_run_tests(
        self,
        task_id: UUID,
        test_types: Optional[List[TestCaseType]] = None,
    ) -> Optional[TestTask]:
        """生成并运行测试

        Args:
            task_id: 测试任务 ID
            test_types: 要生成的测试类型

        Returns:
            TestTask: 更新后的任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if not self._codegen_service:
            raise RuntimeError("CodeGenService not set")

        codegen_task = self._codegen_service.get_task(task.codegen_task_id)
        if not codegen_task:
            task.status = TestStatus.FAILED
            task.error_message = "Code generation task not found"
            task.updated_at = datetime.utcnow()
            return task

        task.status = TestStatus.GENERATING
        task.updated_at = datetime.utcnow()

        try:
            test_cases = test_agent_service.generate_test_cases(
                code_files=codegen_task.files,
                test_types=test_types or [TestCaseType.UNIT],
            )
            task.test_cases = test_cases

        except Exception as e:
            task.status = TestStatus.FAILED
            task.error_message = f"Test generation failed: {str(e)}"
            task.updated_at = datetime.utcnow()
            return task

        if not test_cases:
            task.status = TestStatus.COMPLETED
            task.coverage = CoverageInfo()
            task.updated_at = datetime.utcnow()
            task.completed_at = datetime.utcnow()
            return task

        task.status = TestStatus.RUNNING
        task.updated_at = datetime.utcnow()

        project_id = task.requirement_id
        if self._requirement_service:
            requirement = self._requirement_service.get(task.requirement_id)
            if requirement:
                project_id = requirement.project_id

        sandbox = sandbox_service.create_sandbox(project_id)
        task.sandbox_id = sandbox.sandbox_id

        try:
            for file in codegen_task.files:
                sandbox_service.write_file(
                    sandbox_id=sandbox.sandbox_id,
                    path=file.path,
                    content=file.content,
                )

            results, coverage = test_agent_service.execute_tests(
                test_cases=test_cases,
                sandbox_id=sandbox.sandbox_id,
                sandbox_service=sandbox_service,
            )
            task.results = results
            task.coverage = coverage

            report = test_agent_service.generate_test_report(
                task_id=task.id,
                test_cases=test_cases,
                results=results,
                coverage=coverage,
            )
            self._reports[task.id] = report

            task.status = TestStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()

            return task

        except Exception as e:
            task.status = TestStatus.FAILED
            task.error_message = f"Test execution failed: {str(e)}"
            task.updated_at = datetime.utcnow()
            return task

    def get_test_cases(self, task_id: UUID) -> Optional[List[TestCase]]:
        """获取测试用例列表

        Args:
            task_id: 测试任务 ID

        Returns:
            List[TestCase]: 测试用例列表，任务不存在返回 None
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        return task.test_cases

    def get_test_results(self, task_id: UUID) -> Optional[List[TestResult]]:
        """获取测试结果列表

        Args:
            task_id: 测试任务 ID

        Returns:
            List[TestResult]: 测试结果列表，任务不存在返回 None
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        return task.results

    def get_test_report(self, task_id: UUID) -> Optional[TestReport]:
        """获取测试报告

        Args:
            task_id: 测试任务 ID

        Returns:
            TestReport: 测试报告，不存在返回 None
        """
        if task_id in self._reports:
            return self._reports[task_id]

        task = self._tasks.get(task_id)
        if not task:
            return None

        if task.status != TestStatus.COMPLETED:
            return None

        report = test_agent_service.generate_test_report(
            task_id=task_id,
            test_cases=task.test_cases,
            results=task.results,
            coverage=task.coverage,
        )
        self._reports[task_id] = report

        return report

    async def rerun_tests(
        self,
        task_id: UUID,
        test_case_ids: Optional[List[UUID]] = None,
        fix_failed_tests: bool = False,
    ) -> Optional[TestTask]:
        """重新运行测试

        Args:
            task_id: 测试任务 ID
            test_case_ids: 指定要重新运行的测试用例
            fix_failed_tests: 是否尝试修复失败的测试

        Returns:
            TestTask: 更新后的任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if not task.test_cases:
            return task

        tests_to_run = task.test_cases
        if test_case_ids:
            tests_to_run = [tc for tc in task.test_cases if tc.id in test_case_ids]

        if not tests_to_run:
            return task

        task.status = TestStatus.RUNNING
        task.updated_at = datetime.utcnow()

        if not task.sandbox_id:
            project_id = task.requirement_id
            if self._requirement_service:
                requirement = self._requirement_service.get(task.requirement_id)
                if requirement:
                    project_id = requirement.project_id
            sandbox = sandbox_service.create_sandbox(project_id)
            task.sandbox_id = sandbox.sandbox_id

        try:
            results, coverage = test_agent_service.execute_tests(
                test_cases=tests_to_run,
                sandbox_id=task.sandbox_id,
                sandbox_service=sandbox_service,
            )

            if test_case_ids:
                existing_results = {r.test_case_id: r for r in task.results}
                for result in results:
                    existing_results[result.test_case_id] = result
                task.results = list(existing_results.values())
            else:
                task.results = results

            task.coverage = coverage

            report = test_agent_service.generate_test_report(
                task_id=task.id,
                test_cases=task.test_cases,
                results=task.results,
                coverage=task.coverage,
            )
            self._reports[task.id] = report

            task.status = TestStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()

            return task

        except Exception as e:
            task.status = TestStatus.FAILED
            task.error_message = f"Test rerun failed: {str(e)}"
            task.updated_at = datetime.utcnow()
            return task

    def submit_test_review(
        self,
        task_id: UUID,
        reviewer_notes: Optional[str] = None,
        approve_with_failures: bool = False,
    ) -> Optional[TestTask]:
        """提交测试审核

        Args:
            task_id: 测试任务 ID
            reviewer_notes: 审核备注
            approve_with_failures: 是否允许带失败用例提交

        Returns:
            TestTask: 更新后的任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if task.status != TestStatus.COMPLETED:
            return None

        report = self.get_test_report(task_id)
        if report and report.failed > 0 and not approve_with_failures:
            return None

        task.updated_at = datetime.utcnow()

        return task

    def trigger_ci_pipeline(
        self,
        task_id: UUID,
        target_branch: str = "main",
        run_full_suite: bool = False,
        extra_args: Optional[Dict[str, str]] = None,
    ) -> Optional[CIPipelineInfo]:
        """触发 CI 流水线

        Args:
            task_id: 测试任务 ID
            target_branch: 目标分支
            run_full_suite: 是否运行完整测试套件
            extra_args: 额外参数

        Returns:
            CIPipelineInfo: CI 流水线信息
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if task.status != TestStatus.COMPLETED:
            return None

        pipeline_id = f"pipeline-{uuid4().hex[:8]}"

        pipeline_info = CIPipelineInfo(
            pipeline_id=pipeline_id,
            status="pending",
            url=f"https://ci.example.com/pipelines/{pipeline_id}",
            stages=[
                {"name": "build", "status": "pending"},
                {"name": "test", "status": "pending"},
                {"name": "deploy", "status": "pending"},
            ],
        )

        task.ci_pipeline_id = pipeline_id
        task.updated_at = datetime.utcnow()

        self._ci_pipelines[task.id] = pipeline_info

        return pipeline_info

    def get_ci_pipeline_status(self, task_id: UUID) -> Optional[CIPipelineInfo]:
        """获取 CI 流水线状态

        Args:
            task_id: 测试任务 ID

        Returns:
            CIPipelineInfo: CI 流水线信息
        """
        return self._ci_pipelines.get(task_id)

    def delete_task(self, task_id: UUID) -> bool:
        """删除测试任务

        Args:
            task_id: 任务 ID

        Returns:
            bool: 是否删除成功
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.sandbox_id:
            sandbox_service.cleanup_sandbox(task.sandbox_id)

        codegen_task_id = task.codegen_task_id
        if codegen_task_id in self._codegen_to_tests:
            self._codegen_to_tests[codegen_task_id] = [
                tid for tid in self._codegen_to_tests[codegen_task_id]
                if tid != task_id
            ]

        self._reports.pop(task_id, None)
        self._ci_pipelines.pop(task_id, None)

        del self._tasks[task_id]
        return True

    def get_statistics(self, codegen_task_id: Optional[UUID] = None) -> dict:
        """获取测试统计

        Args:
            codegen_task_id: 代码生成任务 ID（可选）

        Returns:
            dict: 统计数据
        """
        if codegen_task_id:
            tasks = self.get_tasks_by_codegen(codegen_task_id)
        else:
            tasks = list(self._tasks.values())

        by_status = {}
        for status in TestStatus:
            by_status[status.value] = len([t for t in tasks if t.status == status])

        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for task in tasks:
            total_tests += len(task.test_cases)
            for result in task.results:
                if result.status == TestResultStatus.PASSED:
                    total_passed += 1
                elif result.status == TestResultStatus.FAILED:
                    total_failed += 1
                else:
                    total_skipped += 1

        avg_coverage = 0.0
        completed_tasks = [t for t in tasks if t.status == TestStatus.COMPLETED and t.coverage]
        if completed_tasks:
            avg_coverage = sum(t.coverage.lines_percent for t in completed_tasks) / len(completed_tasks)

        ci_triggered = len([t for t in tasks if t.ci_pipeline_id])

        return {
            "total_tasks": len(tasks),
            "by_status": by_status,
            "tests": {
                "total": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
            },
            "average_coverage": round(avg_coverage, 2),
            "ci_pipelines_triggered": ci_triggered,
        }


test_service = TestService()
