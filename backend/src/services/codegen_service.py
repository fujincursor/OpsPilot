"""代码生成服务

负责代码生成任务的管理和协调，包括：
- 创建和管理代码生成任务
- 调用 CodeGenAgent 生成代码
- 在 Sandbox 中运行 Lint 检查
- 生成代码 diff
- 创建 Merge Request
"""

import difflib
from datetime import datetime
from typing import Dict, List, Optional, Union, TYPE_CHECKING
from uuid import UUID

from ..models.codegen import (
    CodeGenTask,
    CodeGenStatus,
    CodeFile,
    FileAction,
    LintResult,
    CodeDiff,
    MergeRequestInfo,
    CodeGenFilters,
)
from ..models.solution import Solution, BugFixSolution, FeatureDesignSolution
from .agents.codegen_agent import codegen_agent_service
from .sandbox_service import sandbox_service

if TYPE_CHECKING:
    from .solution_service import SolutionService
    from .requirement_service import RequirementService


class CodeGenService:
    """代码生成服务

    负责协调代码生成的完整流程：
    1. 创建代码生成任务
    2. 调用 CodeGenAgent 生成代码
    3. 在 Sandbox 中运行 Lint 检查
    4. 生成代码 diff
    5. 创建 Merge Request
    """

    def __init__(self):
        self._tasks: Dict[UUID, CodeGenTask] = {}
        self._solution_to_tasks: Dict[UUID, List[UUID]] = {}
        self._solution_service: Optional["SolutionService"] = None
        self._requirement_service: Optional["RequirementService"] = None

    def set_solution_service(self, solution_service: "SolutionService"):
        """设置方案服务引用"""
        self._solution_service = solution_service

    def set_requirement_service(self, requirement_service: "RequirementService"):
        """设置需求服务引用"""
        self._requirement_service = requirement_service

    def create_codegen_task(
        self,
        solution_id: UUID,
        language: str = "python",
        additional_context: Optional[str] = None,
    ) -> Optional[CodeGenTask]:
        """创建代码生成任务

        Args:
            solution_id: 方案 ID
            language: 主要编程语言
            additional_context: 额外上下文

        Returns:
            CodeGenTask: 创建的任务，方案不存在返回 None
        """
        if not self._solution_service:
            raise RuntimeError("SolutionService not set")

        solution = self._solution_service.get_solution(solution_id)
        if not solution:
            return None

        task = CodeGenTask(
            solution_id=solution_id,
            requirement_id=solution.requirement_id,
            status=CodeGenStatus.PENDING,
            language=language,
        )

        self._tasks[task.id] = task

        if solution_id not in self._solution_to_tasks:
            self._solution_to_tasks[solution_id] = []
        self._solution_to_tasks[solution_id].append(task.id)

        return task

    def get_task(self, task_id: UUID) -> Optional[CodeGenTask]:
        """获取代码生成任务

        Args:
            task_id: 任务 ID

        Returns:
            CodeGenTask: 任务对象，不存在返回 None
        """
        return self._tasks.get(task_id)

    def get_tasks_by_solution(
        self,
        solution_id: UUID,
        filters: Optional[CodeGenFilters] = None,
    ) -> List[CodeGenTask]:
        """获取方案的代码生成任务列表

        Args:
            solution_id: 方案 ID
            filters: 过滤条件

        Returns:
            List[CodeGenTask]: 任务列表
        """
        task_ids = self._solution_to_tasks.get(solution_id, [])
        tasks = [self._tasks[tid] for tid in task_ids if tid in self._tasks]

        if filters:
            if filters.status:
                tasks = [t for t in tasks if t.status == filters.status]
            if filters.language:
                tasks = [t for t in tasks if t.language == filters.language]

        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    async def generate_and_lint(
        self,
        task_id: UUID,
    ) -> Optional[CodeGenTask]:
        """生成代码并运行 Lint 检查

        Args:
            task_id: 任务 ID

        Returns:
            CodeGenTask: 更新后的任务，不存在返回 None
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if not self._solution_service:
            raise RuntimeError("SolutionService not set")

        solution = self._solution_service.get_solution(task.solution_id)
        if not solution:
            task.status = CodeGenStatus.FAILED
            task.error_message = "Solution not found"
            task.updated_at = datetime.utcnow()
            return task

        task.status = CodeGenStatus.GENERATING
        task.updated_at = datetime.utcnow()

        try:
            files = codegen_agent_service.generate_code(solution)
            task.files = files

        except Exception as e:
            task.status = CodeGenStatus.FAILED
            task.error_message = f"Code generation failed: {str(e)}"
            task.updated_at = datetime.utcnow()
            return task

        if not files:
            task.status = CodeGenStatus.COMPLETED
            task.lint_result = LintResult(passed=True)
            task.updated_at = datetime.utcnow()
            task.completed_at = datetime.utcnow()
            return task

        task.status = CodeGenStatus.LINTING
        task.updated_at = datetime.utcnow()

        project_id = task.requirement_id
        if self._requirement_service:
            requirement = self._requirement_service.get(task.requirement_id)
            if requirement:
                project_id = requirement.project_id

        sandbox = sandbox_service.create_sandbox(project_id)
        task.sandbox_id = sandbox.sandbox_id

        try:
            success_count, write_errors = sandbox_service.write_files(
                sandbox_id=sandbox.sandbox_id,
                files=files,
            )

            if write_errors:
                task.status = CodeGenStatus.FAILED
                task.error_message = f"Failed to write files: {', '.join(write_errors[:3])}"
                task.updated_at = datetime.utcnow()
                return task

            lint_result = sandbox_service.run_linter(
                sandbox_id=sandbox.sandbox_id,
                files=files,
            )
            task.lint_result = lint_result

            if lint_result.passed:
                task.status = CodeGenStatus.COMPLETED
                task.completed_at = datetime.utcnow()
            else:
                task.status = CodeGenStatus.COMPLETED
                task.completed_at = datetime.utcnow()

            task.updated_at = datetime.utcnow()
            return task

        except Exception as e:
            task.status = CodeGenStatus.FAILED
            task.error_message = f"Lint check failed: {str(e)}"
            task.updated_at = datetime.utcnow()
            return task

    def get_code_diff(self, task_id: UUID) -> Optional[List[CodeDiff]]:
        """获取代码 diff

        Args:
            task_id: 任务 ID

        Returns:
            List[CodeDiff]: 代码差异列表，任务不存在返回 None
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        diffs = []

        for file in task.files:
            old_content = ""

            if file.action == FileAction.MODIFY:
                old_content = self._get_original_file_content(task, file.path)

            new_content = file.content if file.action != FileAction.DELETE else ""

            diff_text = self._generate_unified_diff(
                old_content=old_content,
                new_content=new_content,
                file_path=file.path,
            )

            diffs.append(CodeDiff(
                file_path=file.path,
                action=file.action,
                old_content=old_content if file.action == FileAction.MODIFY else None,
                new_content=new_content if file.action != FileAction.DELETE else None,
                diff=diff_text,
            ))

        return diffs

    def _get_original_file_content(self, task: CodeGenTask, file_path: str) -> str:
        """获取原始文件内容

        当前返回空字符串，实际应从代码仓库获取。
        """
        return ""

    def _generate_unified_diff(
        self,
        old_content: str,
        new_content: str,
        file_path: str,
    ) -> str:
        """生成 unified diff 格式的差异"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )

        return ''.join(diff)

    def create_merge_request(
        self,
        task_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_branch: str = "main",
    ) -> Optional[MergeRequestInfo]:
        """创建 Merge Request

        Args:
            task_id: 任务 ID
            title: MR 标题
            description: MR 描述
            target_branch: 目标分支

        Returns:
            MergeRequestInfo: MR 信息，任务不存在返回 None
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if task.status != CodeGenStatus.COMPLETED:
            return None

        if not self._solution_service:
            return None

        solution = self._solution_service.get_solution(task.solution_id)
        if not solution:
            return None

        if not title:
            title = f"[Auto] {solution.title}"

        if not description:
            description = self._generate_mr_description(task, solution)

        source_branch = f"auto/codegen-{task.id.hex[:8]}"

        mr_info = MergeRequestInfo(
            mr_id=f"MR-{task.id.hex[:8]}",
            title=title,
            description=description,
            source_branch=source_branch,
            target_branch=target_branch,
            status="open",
        )

        task.mr_info = mr_info
        task.updated_at = datetime.utcnow()

        return mr_info

    def _generate_mr_description(
        self,
        task: CodeGenTask,
        solution: Solution,
    ) -> str:
        """生成 MR 描述"""
        description = f"""## 概述

本 MR 由 OpsPilot 代码生成服务自动创建。

### 关联方案
- 方案 ID: {task.solution_id}
- 方案标题: {solution.title}
- 方案类型: {solution.type.value}

### 生成的文件

"""
        for file in task.files:
            action_str = {
                FileAction.CREATE: "新增",
                FileAction.MODIFY: "修改",
                FileAction.DELETE: "删除",
            }.get(file.action, "未知")
            description += f"- `{file.path}` ({action_str})\n"

        if task.lint_result:
            description += f"""
### Lint 检查结果

- 状态: {'✅ 通过' if task.lint_result.passed else '❌ 未通过'}
- 错误数: {task.lint_result.error_count}
- 警告数: {task.lint_result.warning_count}
"""
            if task.lint_result.errors:
                description += "\n#### 错误详情\n"
                for error in task.lint_result.errors[:5]:
                    description += f"- `{error.file}:{error.line}` - {error.message}\n"

        return description

    async def regenerate_code(
        self,
        task_id: UUID,
        files_to_regenerate: Optional[List[str]] = None,
        fix_lint_errors: bool = True,
        additional_instructions: Optional[str] = None,
    ) -> Optional[CodeGenTask]:
        """重新生成代码

        Args:
            task_id: 任务 ID
            files_to_regenerate: 指定要重新生成的文件
            fix_lint_errors: 是否基于 lint 错误修复
            additional_instructions: 额外指令

        Returns:
            CodeGenTask: 更新后的任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if not self._solution_service:
            raise RuntimeError("SolutionService not set")

        solution = self._solution_service.get_solution(task.solution_id)
        if not solution:
            task.status = CodeGenStatus.FAILED
            task.error_message = "Solution not found"
            task.updated_at = datetime.utcnow()
            return task

        task.status = CodeGenStatus.GENERATING
        task.updated_at = datetime.utcnow()

        try:
            if files_to_regenerate:
                new_files = []
                for file in task.files:
                    if file.path in files_to_regenerate:
                        regenerated = codegen_agent_service.generate_file(
                            solution=solution,
                            file_spec={"path": file.path, "language": file.language},
                        )
                        new_files.append(regenerated)
                    else:
                        new_files.append(file)
                task.files = new_files
            else:
                files = codegen_agent_service.generate_code(solution)
                task.files = files

            if fix_lint_errors and task.lint_result and task.lint_result.errors:
                for error in task.lint_result.errors:
                    for i, file in enumerate(task.files):
                        if file.path == error.file:
                            fix_suggestion = {
                                "type": "auto_fix",
                                "line": error.line,
                                "error_code": error.code,
                                "error_message": error.message,
                            }
                            fixed_code, success = codegen_agent_service.apply_fix(
                                file.content, fix_suggestion
                            )
                            if success:
                                task.files[i] = CodeFile(
                                    path=file.path,
                                    content=fixed_code,
                                    language=file.language,
                                    action=file.action,
                                )
                            break

        except Exception as e:
            task.status = CodeGenStatus.FAILED
            task.error_message = f"Code regeneration failed: {str(e)}"
            task.updated_at = datetime.utcnow()
            return task

        task.status = CodeGenStatus.LINTING
        task.updated_at = datetime.utcnow()

        if task.sandbox_id:
            sandbox = sandbox_service.get_sandbox(task.sandbox_id)
        else:
            project_id = task.requirement_id
            if self._requirement_service:
                requirement = self._requirement_service.get(task.requirement_id)
                if requirement:
                    project_id = requirement.project_id
            sandbox = sandbox_service.create_sandbox(project_id)
            task.sandbox_id = sandbox.sandbox_id

        if sandbox:
            sandbox_service.write_files(
                sandbox_id=task.sandbox_id,
                files=task.files,
            )

            lint_result = sandbox_service.run_linter(
                sandbox_id=task.sandbox_id,
                files=task.files,
            )
            task.lint_result = lint_result

        task.status = CodeGenStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        return task

    def submit_for_review(
        self,
        task_id: UUID,
        reviewer_notes: Optional[str] = None,
        auto_merge: bool = False,
    ) -> Optional[CodeGenTask]:
        """提交代码审核

        Args:
            task_id: 任务 ID
            reviewer_notes: 审核备注
            auto_merge: 是否自动合并

        Returns:
            CodeGenTask: 更新后的任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        if task.status != CodeGenStatus.COMPLETED:
            return None

        if not task.mr_info:
            self.create_merge_request(task_id)

        if task.mr_info:
            if reviewer_notes:
                task.mr_info.description += f"\n\n### 审核备注\n{reviewer_notes}"

            if auto_merge:
                task.mr_info.status = "auto_merge_pending"
            else:
                task.mr_info.status = "pending_review"

            task.updated_at = datetime.utcnow()

        return task

    def get_files(self, task_id: UUID) -> Optional[List[CodeFile]]:
        """获取任务生成的文件列表

        Args:
            task_id: 任务 ID

        Returns:
            List[CodeFile]: 文件列表，任务不存在返回 None
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        return task.files

    def get_lint_result(self, task_id: UUID) -> Optional[LintResult]:
        """获取 Lint 结果

        Args:
            task_id: 任务 ID

        Returns:
            LintResult: Lint 结果，任务不存在返回 None
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        return task.lint_result

    def delete_task(self, task_id: UUID) -> bool:
        """删除代码生成任务

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

        solution_id = task.solution_id
        if solution_id in self._solution_to_tasks:
            self._solution_to_tasks[solution_id] = [
                tid for tid in self._solution_to_tasks[solution_id]
                if tid != task_id
            ]

        del self._tasks[task_id]
        return True

    def get_statistics(self, solution_id: Optional[UUID] = None) -> dict:
        """获取代码生成统计

        Args:
            solution_id: 方案 ID（可选）

        Returns:
            dict: 统计数据
        """
        if solution_id:
            tasks = self.get_tasks_by_solution(solution_id)
        else:
            tasks = list(self._tasks.values())

        by_status = {}
        for status in CodeGenStatus:
            by_status[status.value] = len([t for t in tasks if t.status == status])

        by_language = {}
        for task in tasks:
            lang = task.language
            by_language[lang] = by_language.get(lang, 0) + 1

        lint_passed = len([t for t in tasks if t.lint_result and t.lint_result.passed])
        lint_failed = len([t for t in tasks if t.lint_result and not t.lint_result.passed])

        mr_created = len([t for t in tasks if t.mr_info])

        return {
            "total": len(tasks),
            "by_status": by_status,
            "by_language": by_language,
            "lint": {
                "passed": lint_passed,
                "failed": lint_failed,
            },
            "merge_requests_created": mr_created,
        }


codegen_service = CodeGenService()
