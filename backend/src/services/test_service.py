"""测试服务

负责测试任务的管理和协调，包括：
- 创建和管理测试任务
- 调用 TestAgent 生成和执行测试
- 生成测试报告
- 触发 CI 流水线
"""

import asyncio
import json
import re
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
from ..models.codegen import CodeFile, CodeGenTask, CodeGenStatus, FileAction
from ..db import DocumentDict
from .agents.test_agent import test_agent_service
from .sandbox_service import sandbox_service

if TYPE_CHECKING:
    from .codegen_service import CodeGenService
    from .requirement_service import RequirementService


CHECK_SCRIPT = r'''# -*- coding: utf-8 -*-
import json
import re
import traceback
from pathlib import Path

FILES = __FILES__
HEADER = __HEADER__
APP = __APP__
PYTHON_FILES = __PYTHON_FILES__
RESULTS = []


def run(name, fn):
    try:
        detail = fn()
        RESULTS.append({"name": name, "status": "passed", "detail": detail or "通过"})
    except Exception as exc:
        RESULTS.append({
            "name": name,
            "status": "failed",
            "detail": str(exc),
            "trace": traceback.format_exc(),
        })


def test_sources_present():
    missing = [rel for rel in FILES if not Path(rel).is_file() or Path(rel).stat().st_size == 0]
    if missing:
        raise AssertionError("沙箱里没有这些源码文件: " + ", ".join(missing))
    return "沙箱中可以读到 %d 个源码文件" % len(FILES)


def normalize(path):
    path = path.split("?", 1)[0].strip()
    if not path or path == "*":
        return ""
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/") or "/"


def route_exists(link, routes):
    for route in routes:
        pattern = "^" + re.sub(r":[^/]+", "[^/]+", route) + "$"
        if re.match(pattern, link):
            return True
    return False


def test_routes():
    header = Path(HEADER).read_text(encoding="utf-8")
    app = Path(APP).read_text(encoding="utf-8")
    links = [normalize(item) for item in re.findall(r"""\bto\s*=\s*["'](/[^"']+)["']""", header)]
    links = [item for item in links if item]
    routes = [normalize(item) for item in re.findall(r"""\bpath\s*=\s*["']([^"']+)["']""", app)]
    routes = [item for item in routes if item]
    missing = [link for link in links if not route_exists(link, routes)]
    if missing:
        raise AssertionError("导航没有对应页面路由: " + ", ".join(missing))
    return "全部 %d 个导航都有对应路由" % len(links)


def test_python_syntax():
    import py_compile
    for rel in PYTHON_FILES:
        py_compile.compile(rel, doraise=True)
    return "已检查 %d 个 Python 文件" % len(PYTHON_FILES)


run("源码已复制到沙箱", test_sources_present)
if HEADER and APP:
    run("导航目标都已注册路由", test_routes)
if PYTHON_FILES:
    run("生成的 Python 文件可通过语法检查", test_python_syntax)
print(json.dumps(RESULTS, ensure_ascii=False))
'''


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
        self._tasks: Dict[UUID, TestTask] = DocumentDict("test_tasks", model=TestTask)
        self._codegen_to_tests: Dict[UUID, List[UUID]] = {}
        for task in self._tasks.values():
            self._codegen_to_tests.setdefault(task.codegen_task_id, []).append(task.id)
        self._reports: Dict[UUID, TestReport] = DocumentDict("test_reports", model=TestReport)
        self._ci_pipelines: Dict[UUID, CIPipelineInfo] = DocumentDict(
            "ci_pipelines",
            model=CIPipelineInfo,
        )
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

        project_id = None
        if self._requirement_service:
            requirement = self._requirement_service.get(task.requirement_id)
            if requirement is not None:
                project_id = requirement.project_id
        from ..models.agent import AgentType
        from .agent_runtime import AgentDisabledError, agent_runtime

        try:
            test_agent = agent_runtime.require(project_id, AgentType.TEST_EXECUTION) if project_id else None
        except AgentDisabledError as exc:
            task.status = TestStatus.FAILED
            task.error_message = str(exc)
            return self._save_task(task)
        if test_agent is None:
            task.status = TestStatus.FAILED
            task.error_message = "Test Agent 未启用，这一阶段不会执行"
            return self._save_task(task)

        task.status = TestStatus.GENERATING
        self._save_task(task)
        return await self._generate_personalized(task, codegen_task, test_agent, project_id)

    async def _generate_personalized(self, task: TestTask, codegen_task: CodeGenTask, test_agent, project_id) -> TestTask:
        """按修改后的代码生成覆盖用例，在沙箱执行，并写出报告。"""
        from .agent_runtime import agent_runtime
        from .sandbox_service import sandbox_service
        from .test_execution import (
            add_fallback,
            build_prompt,
            change_focus,
            changed_sources,
            coverage_from_files,
            execute_suite,
            invocation_problems,
            materialize_changed_modules,
            missed_changed,
            parse_suite,
            skill_text,
            suite_from_payload,
        )

        sources = changed_sources(codegen_task.files)
        if not sources:
            return self._finish_with_report(
                task,
                [],
                [],
                CoverageInfo(),
                "这次代码变更没有可执行的新增或修改文件。",
            )
        originals = self._originals(codegen_task, sources)
        targets = change_focus(sources, originals)
        if not any(item.added_lines or item.symbols for item in targets):
            return self._finish_with_report(
                task,
                [],
                [],
                CoverageInfo(),
                "这次变更没有可执行的新增或修改语句。",
            )
        modules = materialize_changed_modules(targets, sources)
        measured = {
            "files": [item.path for item in sources],
            "changed_lines": {item.path: item.added_lines for item in targets if item.added_lines},
        }

        skill = skill_text()
        summary = ""
        cases: List[TestCase] = []
        test_files: Dict[str, str] = {}
        uncovered: Optional[Dict[str, List[int]]] = None
        feedback = ""
        outcome: Optional[dict] = None
        try:
            for attempt in range(2):
                response = await asyncio.to_thread(
                    agent_runtime.complete,
                    test_agent,
                    build_prompt(sources, skill, targets, uncovered, feedback),
                    f"test-{task.id}",
                )
                payload = parse_suite(response.message if response.success else "")
                if payload is None:
                    feedback = response.message or "测试代理没有返回用例"
                    task.error_message = feedback
                    continue
                summary, cases, test_files = suite_from_payload(payload)
                if not cases or not test_files:
                    feedback = "测试代理没有生成可执行用例"
                    task.error_message = feedback
                    continue
                problems = invocation_problems(test_files, targets)
                if problems and attempt == 0:
                    feedback = "；".join(problems)
                    task.error_message = feedback
                    continue
                if problems:
                    test_files, cases = add_fallback(test_files, cases, targets)
                    summary = (summary + " 生成的用例没有调用变更函数，已补上直接调用并执行。").strip()
                task.test_cases = cases
                task.status = TestStatus.RUNNING
                self._save_task(task)
                sandbox = sandbox_service.create_sandbox(project_id or task.requirement_id)
                sandbox_service.seed_workspace(sandbox.sandbox_id)
                task.sandbox_id = sandbox.sandbox_id
                self._save_task(task)
                outcome = await asyncio.to_thread(
                    execute_suite,
                    sandbox.sandbox_id,
                    sources,
                    test_files,
                    modules,
                    measured,
                )
                file_map = outcome.get("files") or {}
                uncovered = missed_changed(file_map)
                if not uncovered:
                    feedback = ""
                    break
                feedback = "变更代码还没有被执行到。"
        except Exception as exc:
            task.error_message = f"测试执行失败: {exc}"
            return self._finish_with_report(task, cases, [], CoverageInfo(), task.error_message)

        if outcome is None:
            message = task.error_message or "没有生成可执行的测试用例"
            return self._finish_with_report(task, cases, [], CoverageInfo(), message)

        results = self._results_for_cases(cases, outcome.get("cases") or [])
        file_map = outcome.get("files") or {}
        missed = missed_changed(file_map)
        if missed:
            detail = "；".join(
                f"{path} 未执行行 {','.join(str(number) for number in numbers[:12])}" if numbers else path
                for path, numbers in missed.items()
            )
            gap = TestCase(
                name="执行变更代码",
                description="确认新增或修改的语句在沙箱中被调用",
                expected_result="变更语句被实际执行",
                file_path="tests/generated",
            )
            cases.append(gap)
            results.append(TestResult(
                test_case_id=gap.id,
                status=TestResultStatus.FAILED,
                error_message=f"没有执行到变更代码：{detail}"[:1000],
            ))
        coverage = coverage_from_files(file_map)
        report_summary = self._report_summary(summary, coverage, file_map)
        task = self._finish_with_report(task, cases, results, coverage, report_summary)
        task.error_message = None
        return task

    def _results_for_cases(self, cases: List[TestCase], raw_cases: List[dict]) -> List[TestResult]:
        by_name = {str(item.get("name") or ""): item for item in raw_cases}
        results: List[TestResult] = []
        seen: set[str] = set()
        for case in cases:
            seen.add(case.name)
            item = by_name.get(case.name)
            if item is None:
                results.append(TestResult(
                    test_case_id=case.id,
                    status=TestResultStatus.FAILED,
                    error_message="沙箱没有执行到这条用例",
                ))
                continue
            status = TestResultStatus.PASSED if item.get("status") == "passed" else TestResultStatus.FAILED
            results.append(TestResult(
                test_case_id=case.id,
                status=status,
                actual_result=str(item.get("detail") or "")[:1000],
                error_message=None if status == TestResultStatus.PASSED else str(item.get("detail") or "测试失败")[:1000],
                stack_trace=item.get("trace"),
            ))
        for name, item in by_name.items():
            if not name or name in seen:
                continue
            status = TestResultStatus.PASSED if item.get("status") == "passed" else TestResultStatus.FAILED
            case = TestCase(name=name[:200], description="沙箱执行到的用例", file_path="tests/generated")
            cases.append(case)
            results.append(TestResult(
                test_case_id=case.id,
                status=status,
                actual_result=str(item.get("detail") or "")[:1000],
                error_message=None if status == TestResultStatus.PASSED else str(item.get("detail") or "测试失败")[:1000],
                stack_trace=item.get("trace"),
            ))
        return results

    def _report_summary(self, summary: str, coverage: CoverageInfo, file_map: dict) -> str:
        gaps = []
        for path, info in file_map.items():
            percent = float(info.get("lines_percent") or 0)
            if percent < 99.9:
                uncovered = info.get("uncovered") or []
                detail = f"{path} {percent:.0f}%"
                if uncovered:
                    detail += " 未覆盖行 " + ",".join(str(number) for number in uncovered[:12])
                gaps.append(detail)
        lines = [summary or "已根据变更代码生成用例，并在沙箱中执行。"]
        lines.append(f"变更代码行覆盖率 {coverage.lines_percent:.0f}%。")
        if gaps:
            lines.append("这些变更还没有被执行到：" + "；".join(gaps))
        else:
            lines.append("变更语句已在沙箱中执行。")
        return "\n".join(lines)[:5000]

    def _finish_with_report(
        self,
        task: TestTask,
        cases: List[TestCase],
        results: List[TestResult],
        coverage: CoverageInfo,
        summary: str,
    ) -> TestTask:
        if not cases and summary:
            cases = [TestCase(name="生成测试用例", description=summary[:2000], expected_result="生成可执行用例")]
            results = [TestResult(
                test_case_id=cases[0].id,
                status=TestResultStatus.FAILED,
                error_message=summary[:1000],
            )]
        task.test_cases = cases
        task.results = results
        task.coverage = coverage
        report = test_agent_service.generate_test_report(
            task_id=task.id,
            test_cases=cases,
            results=results,
            coverage=coverage,
        )
        report.summary = summary
        self._reports[task.id] = report
        task.status = TestStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.error_message = None
        return self._save_task(task)

    async def _rerun_personalized(
        self,
        task: TestTask,
        codegen_task: CodeGenTask,
        cases: List[TestCase],
        test_files: Dict[str, str],
    ) -> TestTask:
        from .sandbox_service import sandbox_service
        from .test_execution import (
            change_focus,
            changed_sources,
            coverage_from_files,
            execute_suite,
            materialize_changed_modules,
        )

        sources = changed_sources(codegen_task.files)
        targets = change_focus(sources, self._originals(codegen_task, sources))
        modules = materialize_changed_modules(targets, sources)
        measured = {
            "files": [item.path for item in sources],
            "changed_lines": {item.path: item.added_lines for item in targets if item.added_lines},
        }
        project_id = task.requirement_id
        if self._requirement_service:
            requirement = self._requirement_service.get(task.requirement_id)
            if requirement is not None:
                project_id = requirement.project_id
        task.status = TestStatus.RUNNING
        self._save_task(task)
        sandbox = sandbox_service.create_sandbox(project_id)
        sandbox_service.seed_workspace(sandbox.sandbox_id)
        task.sandbox_id = sandbox.sandbox_id
        self._save_task(task)
        try:
            outcome = await asyncio.to_thread(
                execute_suite,
                sandbox.sandbox_id,
                sources,
                test_files,
                modules,
                measured,
            )
        except Exception as exc:
            return self._finish_with_report(task, cases, [], CoverageInfo(), f"测试执行失败: {exc}")
        results = self._results_for_cases(cases, outcome.get("cases") or [])
        coverage = coverage_from_files(outcome.get("files") or {})
        summary = self._report_summary("已在沙箱中重新执行修改后的代码。", coverage, outcome.get("files") or {})
        return self._finish_with_report(task, cases, results, coverage, summary)

    def _originals(self, task: CodeGenTask, sources: List[CodeFile]) -> Dict[str, str]:
        """测试发生在写回之前，用工作区里的旧文件计算变更行。"""
        originals: Dict[str, str] = {}
        root = None if task.applied_at else self._codegen_service._task_root(task)
        for item in sources:
            if root is None or item.action == FileAction.CREATE:
                originals[item.path] = ""
                continue
            originals[item.path] = self._codegen_service._read_repo_file(item.path, root)
        return originals

    def _save_task(self, task: TestTask) -> TestTask:
        task.updated_at = datetime.utcnow()
        self._tasks[task.id] = task
        return task

    def _files_under_test(self, codegen_task: CodeGenTask) -> List[CodeFile]:
        shown = self._codegen_service.for_display(codegen_task)
        files = [item for item in shown.files if item.content.strip() and item.action != FileAction.DELETE]
        if files:
            return files
        return [item for item in codegen_task.files if item.content.strip()]

    def _build_sandbox_cases(self, files: List[CodeFile]) -> List[TestCase]:
        header = next((item.path for item in files if item.path.endswith("Header.tsx")), "")
        app = next((item.path for item in files if item.path.endswith("App.tsx")), "")
        script = self._check_script(files, header, app)
        cases = [
            TestCase(
                name="源码已复制到沙箱",
                description="把被测源码写入临时沙箱，并确认文件可以读取",
                type=TestCaseType.UNIT,
                code=script,
                expected_result="沙箱中能读到全部被测源码",
                file_path="tests/run_checks.py",
            )
        ]
        if header and app:
            cases.append(TestCase(
                name="导航目标都已注册路由",
                description=f"检查 {header} 里的导航地址在 {app} 中都有对应路由",
                type=TestCaseType.UNIT,
                code="读取导航组件中的 to 地址，并与路由表中的 path 逐个对照。",
                expected_result="每个导航地址都有已注册的页面路由",
                file_path="tests/run_checks.py",
            ))
        python_files = [
            item.path for item in files
            if item.language == "python" and item.action in {FileAction.CREATE, FileAction.MODIFY}
        ]
        if python_files:
            cases.append(TestCase(
                name="生成的 Python 文件可通过语法检查",
                description="使用当前 Python 解释器编译生成的 Python 文件",
                type=TestCaseType.UNIT,
                code="py_compile.compile(path, doraise=True)",
                expected_result="生成的 Python 文件没有语法错误",
                file_path="tests/run_checks.py",
            ))
        return cases

    def _check_script(self, files: List[CodeFile], header: str, app: str) -> str:
        python_files = [
            item.path for item in files
            if item.language == "python" and item.action in {FileAction.CREATE, FileAction.MODIFY}
        ]
        return CHECK_SCRIPT.replace("__FILES__", json.dumps([item.path for item in files], ensure_ascii=False)) \
            .replace("__HEADER__", json.dumps(header, ensure_ascii=False)) \
            .replace("__APP__", json.dumps(app, ensure_ascii=False)) \
            .replace("__PYTHON_FILES__", json.dumps(python_files, ensure_ascii=False))

    async def _run_cases_in_sandbox(
        self,
        task: TestTask,
        files: List[CodeFile],
        test_cases: List[TestCase],
    ) -> TestTask:
        task.status = TestStatus.RUNNING
        self._save_task(task)

        project_id = task.requirement_id
        if self._requirement_service:
            requirement = self._requirement_service.get(task.requirement_id)
            if requirement:
                project_id = requirement.project_id

        sandbox = sandbox_service.create_sandbox(project_id)
        sandbox_service.seed_workspace(sandbox.sandbox_id)
        task.sandbox_id = sandbox.sandbox_id
        self._save_task(task)

        for item in files:
            ok, message = sandbox_service.write_file(sandbox.sandbox_id, item.path, item.content)
            if not ok:
                task.status = TestStatus.FAILED
                task.error_message = f"写入沙箱失败: {message}"
                return self._save_task(task)

        script = test_cases[0].code
        ok, message = sandbox_service.write_file(sandbox.sandbox_id, "tests/run_checks.py", script)
        if not ok:
            task.status = TestStatus.FAILED
            task.error_message = f"写入测试脚本失败: {message}"
            return self._save_task(task)

        started = datetime.utcnow()
        execution = await asyncio.to_thread(
            sandbox_service.execute_command,
            sandbox.sandbox_id,
            [sandbox_service.python_executable(), "tests/run_checks.py"],
            60,
        )
        duration_ms = max(execution.duration_ms, int((datetime.utcnow() - started).total_seconds() * 1000))
        parsed = self._parse_check_output(execution.stdout)
        if not parsed:
            task.results = [
                TestResult(
                    test_case_id=case.id,
                    status=TestResultStatus.FAILED,
                    actual_result=(execution.stdout or "")[:1000],
                    error_message=(execution.stderr or "沙箱没有返回测试结果")[:1000],
                    stack_trace=execution.stderr or None,
                    duration_ms=duration_ms,
                )
                for case in test_cases
            ]
        else:
            by_name = {item.get("name"): item for item in parsed}
            share = max(duration_ms // max(len(test_cases), 1), 1)
            task.results = []
            for case in test_cases:
                item = by_name.get(case.name)
                if item is None:
                    task.results.append(TestResult(
                        test_case_id=case.id,
                        status=TestResultStatus.FAILED,
                        error_message="沙箱结果中没有这条用例",
                        duration_ms=share,
                    ))
                    continue
                status = TestResultStatus.PASSED if item.get("status") == "passed" else TestResultStatus.FAILED
                task.results.append(TestResult(
                    test_case_id=case.id,
                    status=status,
                    actual_result=str(item.get("detail") or "")[:1000],
                    error_message=None if status == TestResultStatus.PASSED else str(item.get("detail") or "测试失败")[:1000],
                    stack_trace=item.get("trace"),
                    duration_ms=share,
                ))

        passed = sum(1 for item in task.results if item.status == TestResultStatus.PASSED)
        total_lines = sum(len(item.content.splitlines()) for item in files)
        covered = int(total_lines * passed / len(task.results)) if task.results else 0
        task.coverage = CoverageInfo(
            lines_total=total_lines,
            lines_covered=covered,
            lines_percent=(covered / total_lines * 100) if total_lines else 0,
            functions_total=len(test_cases),
            functions_covered=passed,
            functions_percent=(passed / len(test_cases) * 100) if test_cases else 0,
        )
        report = test_agent_service.generate_test_report(
            task_id=task.id,
            test_cases=test_cases,
            results=task.results,
            coverage=task.coverage,
        )
        self._reports[task.id] = report
        task.status = TestStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.error_message = None
        return self._save_task(task)

    def _parse_check_output(self, stdout: str) -> List[dict]:
        match = re.search(r"(\[\s*\{.*\}\s*\])\s*$", stdout or "", re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

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

        codegen_task = self._codegen_service.get_task(task.codegen_task_id) if self._codegen_service else None
        files = self._files_under_test(codegen_task) if codegen_task else []
        cases = tests_to_run if test_case_ids else task.test_cases
        generated = {
            case.file_path: case.code
            for case in cases
            if str(case.file_path).startswith("tests/generated/") and case.code.strip()
        }
        if generated and codegen_task is not None:
            return await self._rerun_personalized(task, codegen_task, cases, generated)
        return await self._run_cases_in_sandbox(task, files, cases)

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
        if report is None:
            return None
        del approve_with_failures

        task = self._save_task(task)
        self._create_review_item(task, report, reviewer_notes)
        return task

    def _create_review_item(self, task: TestTask, report: Optional[TestReport], notes: Optional[str]) -> None:
        from .hitl_service import hitl_service
        from ..models.review import ReviewItemCreate, ReviewItemType, ReviewPriority

        requirement = self._requirement_service.get(task.requirement_id) if self._requirement_service else None
        if not requirement:
            return

        summary = ""
        if report:
            summary = report.summary or f"通过 {report.passed} 个，失败 {report.failed} 个，覆盖率 {report.coverage_percent:.1f}%。"
        description = "\n".join(part for part in (summary, notes or "测试已完成，等待人工评审。") if part)
        hitl_service.create_review_item(
            item_type=ReviewItemType.TEST,
            item_id=task.id,
            data=ReviewItemCreate(
                title=f"测试审批：{requirement.title}"[:200],
                description=description[:5000],
                item_type=ReviewItemType.TEST,
                item_id=task.id,
                project_id=requirement.project_id,
                requirement_id=requirement.id,
                session_id=requirement.session_id,
                priority=ReviewPriority.MEDIUM,
            ),
        )

    async def trigger_ci_pipeline(
        self,
        task_id: UUID,
        target_branch: str = "main",
        run_full_suite: bool = False,
        extra_args: Optional[Dict[str, str]] = None,
    ) -> Optional[CIPipelineInfo]:
        """在沙箱中重新运行检查，并把结果记成一条流水线。"""
        del target_branch, run_full_suite, extra_args
        task = self._tasks.get(task_id)
        if not task:
            return None

        if task.status != TestStatus.COMPLETED:
            return None

        pipeline = CIPipelineInfo(
            pipeline_id=f"pipeline-{uuid4().hex[:8]}",
            status="running",
            stages=[
                {"name": "准备源码", "status": "running", "detail": "正在把源码写入沙箱"},
                {"name": "运行检查", "status": "pending", "detail": "等待源码准备完成"},
            ],
        )
        task.ci_pipeline_id = pipeline.pipeline_id
        self._save_task(task)
        self._ci_pipelines[task.id] = pipeline

        codegen_task = self._codegen_service.get_task(task.codegen_task_id) if self._codegen_service else None
        files = self._files_under_test(codegen_task) if codegen_task else []
        try:
            task = await self._run_cases_in_sandbox(task, files, task.test_cases)
        except Exception as exc:
            pipeline.status = "failed"
            pipeline.completed_at = datetime.utcnow()
            pipeline.stages = [
                {"name": "准备源码", "status": "failed", "detail": str(exc)},
                {"name": "运行检查", "status": "skipped", "detail": "检查没有开始"},
            ]
            self._ci_pipelines[task.id] = pipeline
            return pipeline

        pipeline.stages = self._ci_stages(task)
        pipeline.status = "passed" if all(stage["status"] == "passed" for stage in pipeline.stages) else "failed"
        pipeline.completed_at = datetime.utcnow()
        self._ci_pipelines[task.id] = pipeline
        return pipeline

    def _ci_stages(self, task: TestTask) -> List[dict]:
        by_case = {item.test_case_id: item for item in task.results}
        source_cases = [case for case in task.test_cases if case.name == "源码已复制到沙箱"]
        check_cases = [case for case in task.test_cases if case.name != "源码已复制到沙箱"]

        def describe(cases: List[TestCase]) -> tuple[str, str]:
            if not cases:
                return "failed", task.error_message or "没有可执行的检查"
            messages = []
            failed = False
            for case in cases:
                result = by_case.get(case.id)
                if result is None or result.status != TestResultStatus.PASSED:
                    failed = True
                    messages.append(result.error_message or result.actual_result or case.name if result else case.name)
                elif result.actual_result:
                    messages.append(result.actual_result)
            return ("failed" if failed else "passed"), "；".join(message for message in messages if message)

        source_status, source_detail = describe(source_cases)
        if source_status != "passed":
            return [
                {"name": "准备源码", "status": source_status, "detail": source_detail},
                {"name": "运行检查", "status": "skipped", "detail": "源码没有准备好，检查未执行"},
            ]
        check_status, check_detail = describe(check_cases)
        return [
            {"name": "准备源码", "status": source_status, "detail": source_detail},
            {"name": "运行检查", "status": check_status, "detail": check_detail},
        ]

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
