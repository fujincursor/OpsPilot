"""代码生成服务

负责代码生成任务的管理和协调，包括：
- 创建和管理代码生成任务
- 按方案步骤逐步生成代码
- 在 Sandbox 中运行 Lint 检查
- 生成代码 diff
- 创建 Merge Request
"""

import asyncio
import difflib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, TYPE_CHECKING
from uuid import UUID

from ..models.codegen import (
    CodeGenTask,
    CodeGenStatus,
    CodeGenStep,
    CodeGenStepStatus,
    CodeFile,
    CodeLocation,
    DiffLine,
    FileAction,
    LintResult,
    CodeDiff,
    MergeRequestInfo,
    CodeGenFilters,
)
from ..models.solution import Solution, BugFixSolution, FeatureDesignSolution, SolutionType

logger = logging.getLogger(__name__)
from ..db import DocumentDict
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
        self._tasks: Dict[UUID, CodeGenTask] = DocumentDict("codegen_tasks", model=CodeGenTask)
        self._solution_to_tasks: Dict[UUID, List[UUID]] = {}
        for task in self._tasks.values():
            self._solution_to_tasks.setdefault(task.solution_id, []).append(task.id)
        self._solution_service: Optional["SolutionService"] = None
        self._requirement_service: Optional["RequirementService"] = None
        self._running: set[UUID] = set()

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

    def _save_task(self, task: CodeGenTask) -> CodeGenTask:
        task.updated_at = datetime.utcnow()
        self._tasks[task.id] = task
        return task

    def apply_to_project(self, task_id: UUID) -> Optional[CodeGenTask]:
        """把任务里保存的新增、修改和删除写回项目目录。"""
        task = self._tasks.get(task_id)
        if not task or task.status != CodeGenStatus.COMPLETED:
            return None

        applicable = [item for item in task.files if item.action != FileAction.VIEW]
        if not applicable:
            raise ValueError("没有可写回项目的代码文件")

        applied: List[str] = []
        for item in applicable:
            target = self._project_file(item.path)
            if item.action == FileAction.DELETE:
                if target.is_file():
                    target.unlink()
                applied.append(item.path)
                continue
            if not item.content.strip():
                raise ValueError(f"{item.path} 没有内容，已停止写回")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.content, encoding="utf-8", newline="\n")
            applied.append(item.path)

        task.applied_paths = applied
        task.applied_at = datetime.utcnow()
        return self._save_task(task)

    def _project_file(self, relative: str) -> Path:
        raw = relative.replace("\\", "/").strip()
        if not raw or raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
            raise ValueError(f"不允许的路径: {relative}")
        parts = [part for part in raw.split("/") if part not in ("", ".")]
        blocked = {".git", "node_modules", "venv", ".venv", "deerflow", "__pycache__", "data"}
        if not parts or any(part == ".." or part in blocked for part in parts):
            raise ValueError(f"不允许的路径: {relative}")
        root = Path(__file__).resolve().parents[3]
        target = root.joinpath(*parts).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"路径超出项目目录: {relative}")
        return target

    def _is_locate_step(self, title: str) -> bool:
        return any(word in title for word in ("定位", "代码位置", "文件位置", "相关代码"))

    def _must_write_files(self, title: str) -> bool:
        return any(word in title for word in ("实现", "编写", "实施"))

    def _retry_prompt(self, step: CodeGenStep, steps: List[CodeGenStep]) -> str:
        sources = self._located_sources(steps) or "还没有定位到文件。"
        return f"""上一次没有输出代码文件。请只完成当前步骤，并只输出一个 json 代码块。

当前步骤：{step.title}

{sources}

规则：
- files 不能为空。
- 只修改上面已经给出的现有文件，action 使用 modify，content 写修改后的完整内容。
- 不要创建 models/resource.py，也不要使用 /{{resource}} 这种占位路径。
- 监控页面要展示系统里已经保存的数据。
格式：
```json
{{"summary":"改了什么","files":[{{"path":"相对路径","content":"完整文件","language":"tsx","action":"modify"}}]}}
```
"""

    def _locate_step(self, solution, requirement) -> tuple[str, List[CodeLocation]]:
        from pathlib import Path

        from .code_locator import locate_code

        texts = [solution.title, solution.content[:2000]]
        if requirement is not None:
            texts.extend([
                getattr(requirement, "title", "") or "",
                getattr(requirement, "description", "") or "",
            ])
        root = Path(__file__).resolve().parents[3]
        return locate_code(root, texts)

    def _step_record(self, step: CodeGenStep) -> str:
        lines = [f"第 {step.index} 步 {step.title}", step.output]
        for location in step.locations:
            lines.append(f"- {location.path}:{location.line} {location.reason}")
        return "\n".join(line for line in lines if line)

    def _solution_steps(self, solution: Union[Solution, BugFixSolution, FeatureDesignSolution]) -> List[str]:
        """从方案中取出要按顺序执行的步骤。"""
        raw: List[str] = []
        if solution.type == SolutionType.BUGFIX:
            raw = list(getattr(solution, "fix_steps", []) or [])
        elif solution.type == SolutionType.FEATURE_DESIGN:
            raw = self._feature_steps(solution)

        if not raw:
            for line in solution.content.splitlines():
                stripped = line.strip()
                if re.match(r"^\d+[\.、]\s*\S", stripped):
                    raw.append(stripped)

        cleaned: List[str] = []
        for item in raw:
            text = re.sub(r"^\d+[\.、]\s*", "", str(item).strip())
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned or [solution.title]

    def _feature_steps(self, solution) -> List[str]:
        """按已确认的设计生成和 Bug 修复同样可执行的步骤。"""
        steps = ["定位相关代码位置"]
        components = [
            getattr(item, "name", "") or "组件"
            for item in (getattr(solution, "architecture", []) or [])
        ]
        if components:
            steps.append("按确认方案实现架构组件：" + "、".join(components))
        endpoints = [
            f"{item.method} {item.path}".strip()
            for item in (getattr(solution, "api_design", []) or [])
            if getattr(item, "method", "") or getattr(item, "path", "")
        ]
        if endpoints:
            steps.append("按确认方案实现接口：" + "、".join(endpoints))
        tables = [
            getattr(item, "table_name", "") or "数据表"
            for item in (getattr(solution, "database_changes", []) or [])
        ]
        if tables:
            steps.append("按确认方案完成数据库变更：" + "、".join(tables))
        for phase in getattr(solution, "implementation_phases", []) or []:
            text = str(phase).strip()
            if text and not re.match(r"^phase\s+\d+\s*:", text, re.IGNORECASE):
                steps.append(text)
        steps.append("按确认方案编写完整代码文件")
        return steps

    def _solution_context(self, solution, requirement) -> str:
        parts = [
            f"标题: {solution.title}",
            f"类型: {solution.type.value}",
            f"方案正文:\n{solution.content[:8000]}",
        ]
        if requirement is not None and getattr(requirement, "description", ""):
            parts.append(f"需求描述:\n{requirement.description[:2000]}")
        root_cause = getattr(solution, "root_cause", "")
        if root_cause:
            parts.append(f"根因:\n{root_cause}")
        risk = getattr(solution, "regression_risk", "")
        if risk:
            parts.append(f"回归风险:\n{risk}")
        affected = getattr(solution, "affected_files", []) or []
        if affected:
            parts.append("方案标注的受影响文件:\n" + "\n".join(affected))
        components = getattr(solution, "architecture", []) or []
        if components:
            lines = [
                f"- {getattr(item, 'name', '组件')}: {getattr(item, 'description', '')}"
                for item in components
            ]
            parts.append("已确认的架构组件:\n" + "\n".join(lines))
        endpoints = getattr(solution, "api_design", []) or []
        if endpoints:
            lines = [
                f"- {item.method} {item.path}: {getattr(item, 'description', '')}"
                for item in endpoints
            ]
            parts.append("已确认的接口:\n" + "\n".join(lines))
        changes = getattr(solution, "database_changes", []) or []
        if changes:
            lines = [
                f"- {getattr(item, 'change_type', '')} {item.table_name}: {getattr(item, 'description', '')}"
                for item in changes
            ]
            parts.append("已确认的数据库变更:\n" + "\n".join(lines))
        rollback = getattr(solution, "rollback_plan", "")
        if rollback:
            parts.append(f"回滚方案:\n{rollback[:1000]}")
        return "\n\n".join(parts)

    def _knowledge_context(self, project_id: Optional[UUID], query: str) -> str:
        if project_id is None:
            return ""
        try:
            from .knowledge_service import knowledge_service

            hits = knowledge_service.search_knowledge(
                project_id,
                query,
                top_k=3,
                snippet_chars=500,
            )
        except Exception:
            logger.exception("读取项目知识库失败")
            return ""
        if not hits:
            return ""
        lines = []
        for hit in hits:
            lines.append(f"- {hit.title}: {hit.content_snippet}")
        return "\n\n## 项目知识库\n" + "\n".join(lines)

    def _step_prompt(
        self,
        solution,
        requirement,
        steps: List[CodeGenStep],
        step: CodeGenStep,
        previous: List[str],
        files: List[CodeFile],
        project_id: Optional[UUID],
        additional_instructions: Optional[str],
    ) -> str:
        titles = "\n".join(f"{item.index}. {item.title}" for item in steps)
        done = "\n\n".join(previous) or "还没有已完成的步骤。"
        paths = "\n".join(f"- {item.path}" for item in files) or "还没有生成文件。"
        extra = f"\n\n补充要求:\n{additional_instructions}" if additional_instructions else ""
        knowledge = self._knowledge_context(project_id, f"{solution.title}\n{step.title}")
        sources = self._located_sources(steps)
        return f"""你是代码生成代理。请只执行方案中的当前步骤，不要提前完成后面的步骤。

## 方案
{self._solution_context(solution, requirement)}

## 全部步骤
{titles}

## 已完成步骤
{done}

## 已生成文件
{paths}
{sources}
{knowledge}

## 当前步骤
第 {step.index} 步：{step.title}

只输出一个 json 代码块，不要写代码块以外的说明。格式：
```json
{{"summary":"这一步的结论","files":[{{"path":"相对路径","content":"完整文件内容","language":"python","action":"create"}}]}}
```
规则：
- summary 用中文说明这一步实际做了什么。
- 调查、确认、评审类步骤如果不需要改代码，files 用空数组。
- 步骤标题包含「实现」「编写」或「实施」时，files 不能为空，必须给出新增或修改后的完整文件。
- 方案中的 resource.py、/{{resource}} 这类占位路径如果仓库里不存在，不要创建这些占位文件。
- 需要写代码时，content 必须是该文件的完整内容。
- action 只能是 create、modify、delete。
- path 使用相对路径，不要使用盘符，也不要包含 .. 。
- 把要落地的文件放进 files，不要直接修改仓库。
- 修改已有功能时，改已定位到的真实文件。监控页面就修改已定位的页面，让页面数据来自系统里已经保存的记录。
- 需要修改已有文件时，基于上面给出的现有内容输出修改后的完整文件，action 使用 modify。{extra}
"""

    def _parse_step_output(self, text: str) -> tuple[str, List[CodeFile]]:
        payload = self._extract_step_payload(text)
        if payload is None:
            visible = text.strip()
            return visible[:4000], []

        summary = " ".join(str(payload.get("summary") or "").split())
        files: List[CodeFile] = []
        raw_files = payload.get("files") or []
        if isinstance(raw_files, list):
            for item in raw_files[:20]:
                parsed = self._parse_code_file(item)
                if parsed is not None:
                    files.append(parsed)
        if not summary:
            summary = text.strip()[:4000]
        return summary[:4000], files

    def _extract_step_payload(self, text: str) -> Optional[dict]:
        chunks = re.findall(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        sources = chunks or [text]
        found: Optional[dict] = None
        for chunk in sources:
            start = chunk.find("{")
            while start != -1:
                try:
                    obj, end = json.JSONDecoder().raw_decode(chunk[start:])
                except json.JSONDecodeError:
                    start = chunk.find("{", start + 1)
                    continue
                if isinstance(obj, dict) and ("files" in obj or "summary" in obj):
                    found = obj
                start = chunk.find("{", start + end)
        return found

    def _parse_code_file(self, item) -> Optional[CodeFile]:
        if not isinstance(item, dict):
            return None
        path = self._safe_path(str(item.get("path") or ""))
        if path is None:
            return None
        action_text = str(item.get("action") or "create").lower()
        if action_text not in {action.value for action in FileAction}:
            action_text = FileAction.CREATE.value
        content = str(item.get("content") or "")
        if len(content) > 200_000:
            content = content[:200_000]
        language = str(item.get("language") or "").strip() or self._language_from_path(path)
        return CodeFile(
            path=path,
            content=content,
            language=language,
            action=FileAction(action_text),
        )

    def _safe_path(self, path: str) -> Optional[str]:
        cleaned = path.replace("\\", "/").strip()
        if not cleaned or "://" in cleaned or re.match(r"^[A-Za-z]:", cleaned):
            return None
        cleaned = cleaned.lstrip("/")
        parts = [part for part in cleaned.split("/") if part not in {"", "."}]
        if not parts or any(part == ".." for part in parts):
            return None
        return "/".join(parts)

    def _language_from_path(self, path: str) -> str:
        extension = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        return {
            "py": "python",
            "ts": "typescript",
            "tsx": "tsx",
            "js": "javascript",
            "jsx": "jsx",
            "go": "go",
            "java": "java",
            "sql": "sql",
            "md": "markdown",
            "json": "json",
            "yml": "yaml",
            "yaml": "yaml",
            "css": "css",
            "html": "html",
        }.get(extension, "text")

    def _merge_files(self, current: List[CodeFile], updates: List[CodeFile]) -> List[CodeFile]:
        merged = {item.path: item for item in current}
        for item in updates:
            if item.action == FileAction.DELETE:
                merged.pop(item.path, None)
            else:
                merged[item.path] = item
        return list(merged.values())

    async def generate_and_lint(
        self,
        task_id: UUID,
        additional_instructions: Optional[str] = None,
    ) -> Optional[CodeGenTask]:
        """按方案步骤生成代码，并运行 Lint 检查。"""
        task = self._tasks.get(task_id)
        if not task:
            return None
        if task_id in self._running:
            return task

        if not self._solution_service:
            raise RuntimeError("SolutionService not set")

        solution = self._solution_service.get_solution(task.solution_id)
        if not solution:
            task.status = CodeGenStatus.FAILED
            task.error_message = "Solution not found"
            return self._save_task(task)

        self._running.add(task_id)
        try:
            return await self._generate_steps(task, solution, additional_instructions)
        finally:
            self._running.discard(task_id)

    async def _generate_steps(
        self,
        task: CodeGenTask,
        solution,
        additional_instructions: Optional[str],
    ) -> CodeGenTask:
        from .deerflow_service import deerflow_service

        requirement = None
        project_id = None
        if self._requirement_service:
            requirement = self._requirement_service.get(task.requirement_id)
            if requirement is not None:
                project_id = requirement.project_id

        titles = self._solution_steps(solution)
        task.steps = [
            CodeGenStep(index=index, title=title)
            for index, title in enumerate(titles, start=1)
        ]
        task.files = []
        task.lint_result = None
        task.error_message = None
        task.completed_at = None
        task.status = CodeGenStatus.GENERATING
        self._save_task(task)

        from ..models.agent import AgentType
        from .agent_runtime import AgentDisabledError, agent_runtime

        try:
            codegen_agent = agent_runtime.require(project_id, AgentType.CODE_GENERATION) if project_id else None
        except AgentDisabledError as exc:
            task.status = CodeGenStatus.FAILED
            task.error_message = str(exc)
            return self._save_task(task)
        if codegen_agent is None:
            task.status = CodeGenStatus.FAILED
            task.error_message = "CodeGen Agent 未启用，这一阶段不会执行"
            return self._save_task(task)

        previous: List[str] = []
        for step in task.steps:
            step.status = CodeGenStepStatus.RUNNING
            self._save_task(task)
            logger.info("开始执行方案步骤 %s/%s: %s", step.index, len(task.steps), step.title)
            if self._is_locate_step(step.title):
                summary, locations = self._locate_step(solution, requirement)
                step.output = summary
                step.locations = locations
                step.status = CodeGenStepStatus.COMPLETED
                previous.append(self._step_record(step))
                self._save_task(task)
                continue
            prompt = self._step_prompt(
                solution,
                requirement,
                task.steps,
                step,
                previous,
                task.files,
                project_id,
                additional_instructions,
            )
            response = await asyncio.to_thread(
                deerflow_service.complete,
                agent_runtime.render_task(codegen_agent, prompt),
                f"codegen-{task.id}",
                model_name=codegen_agent.model_name,
            )
            if not response.success:
                step.status = CodeGenStepStatus.FAILED
                step.error_message = response.message
                task.status = CodeGenStatus.FAILED
                task.error_message = f"第 {step.index} 步失败: {response.message}"
                return self._save_task(task)

            summary, files = self._parse_step_output(response.message)
            if not files and self._must_write_files(step.title):
                retry = await asyncio.to_thread(
                    deerflow_service.complete,
                    agent_runtime.render_task(codegen_agent, self._retry_prompt(step, task.steps)),
                    f"codegen-{task.id}",
                    model_name=codegen_agent.model_name,
                )
                if retry.success:
                    summary, files = self._parse_step_output(retry.message)
            step.output = summary
            step.files = files
            step.status = CodeGenStepStatus.COMPLETED
            task.files = self._merge_files(task.files, files)
            previous.append(self._step_record(step))
            self._save_task(task)

        return await self._lint_generated_files(task, project_id or task.requirement_id)

    async def _lint_generated_files(self, task: CodeGenTask, project_id: UUID) -> CodeGenTask:
        files = task.files
        if not files:
            task.status = CodeGenStatus.COMPLETED
            task.lint_result = LintResult(passed=True)
            task.completed_at = datetime.utcnow()
            return self._save_task(task)

        task.status = CodeGenStatus.LINTING
        self._save_task(task)

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
                return self._save_task(task)

            lint_result = sandbox_service.run_linter(
                sandbox_id=sandbox.sandbox_id,
                files=files,
            )
            task.lint_result = lint_result

            task.status = CodeGenStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            return self._save_task(task)

        except Exception as e:
            task.status = CodeGenStatus.FAILED
            task.error_message = f"Lint check failed: {str(e)}"
            return self._save_task(task)

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

    def for_display(self, task: CodeGenTask) -> CodeGenTask:
        """给页面补上可展示的源码和差异，不写回数据库。"""
        shown = task.model_copy(deep=True)
        shown.files = self._files_for_display(task)
        return shown

    def _files_for_display(self, task: CodeGenTask) -> List[CodeFile]:
        files: List[CodeFile] = []
        seen: set[str] = set()
        for item in task.files:
            original = self._read_repo_file(item.path)
            copied = item.model_copy(deep=True)
            new_content = "" if item.action == FileAction.DELETE else item.content
            old_content = "" if item.action == FileAction.CREATE and not original else original
            copied.diff = self._line_diff(old_content, new_content)
            files.append(copied)
            seen.add(item.path)

        for location in self._task_locations(task):
            if location.path in seen:
                continue
            content = self._read_repo_file(location.path)
            if not content:
                continue
            files.append(CodeFile(
                path=location.path,
                content=content,
                language=self._language_from_path(location.path),
                action=FileAction.VIEW,
                diff=self._focused_diff(content, location.line),
            ))
            seen.add(location.path)
        return files

    def _task_locations(self, task: CodeGenTask) -> List[CodeLocation]:
        locations: List[CodeLocation] = []
        seen: set[tuple[str, int]] = set()
        for step in task.steps:
            for location in step.locations:
                key = (location.path, location.line)
                if key in seen:
                    continue
                seen.add(key)
                locations.append(location)
        return self._without_weak_locations(locations)

    def _prefer_step_locations(self, steps: List[CodeGenStep]) -> List[CodeLocation]:
        locations: List[CodeLocation] = []
        seen: set[tuple[str, int]] = set()
        for step in steps:
            for location in step.locations:
                key = (location.path, location.line)
                if key in seen:
                    continue
                seen.add(key)
                locations.append(location)
        return self._without_weak_locations(locations)

    def _without_weak_locations(self, locations: List[CodeLocation]) -> List[CodeLocation]:
        strong = [item for item in locations if "文件内容与问题描述匹配" not in item.reason]
        return strong or locations

    def _located_sources(self, steps: List[CodeGenStep]) -> str:
        sections: List[str] = []
        seen: set[str] = set()
        for location in self._prefer_step_locations(steps):
            if location.path in seen:
                continue
            content = self._read_repo_file(location.path)
            if not content:
                continue
            seen.add(location.path)
            sections.append(f"### {location.path}\n```\n{content[:12000]}\n```")
        if not sections:
            return ""
        return "\n\n## 已定位文件的现有内容\n" + "\n\n".join(sections)

    def _read_repo_file(self, relative: str) -> str:
        safe = self._safe_path(relative)
        if not safe:
            return ""
        root = Path(__file__).resolve().parents[3]
        path = (root / safe).resolve()
        if not path.is_file() or root.resolve() not in path.parents:
            return ""
        if path.stat().st_size > 1_000_000:
            return ""
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    def _line_diff(self, old_content: str, new_content: str) -> List[DiffLine]:
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        rows: List[DiffLine] = []
        matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines)
        old_number = 1
        new_number = 1
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for line in old_lines[i1:i2]:
                    rows.append(DiffLine(type="context", content=line, line_number=old_number))
                    old_number += 1
                    new_number += 1
            elif tag == "delete":
                for line in old_lines[i1:i2]:
                    rows.append(DiffLine(type="remove", content=line, line_number=old_number))
                    old_number += 1
            elif tag == "insert":
                for line in new_lines[j1:j2]:
                    rows.append(DiffLine(type="add", content=line, line_number=new_number))
                    new_number += 1
            else:
                for line in old_lines[i1:i2]:
                    rows.append(DiffLine(type="remove", content=line, line_number=old_number))
                    old_number += 1
                for line in new_lines[j1:j2]:
                    rows.append(DiffLine(type="add", content=line, line_number=new_number))
                    new_number += 1
        return rows

    def _focused_diff(self, content: str, line: int) -> List[DiffLine]:
        rows = content.splitlines()
        if not rows:
            return []
        start = max(1, line - 8)
        end = min(len(rows), line + 8)
        return [
            DiffLine(type="context", content=rows[number - 1], line_number=number)
            for number in range(start, end + 1)
        ]

    def _get_original_file_content(self, task: CodeGenTask, file_path: str) -> str:
        """获取仓库里的原始文件内容。"""
        return self._read_repo_file(file_path)

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
            return self._save_task(task)

        if not files_to_regenerate:
            return await self.generate_and_lint(
                task_id,
                additional_instructions=additional_instructions,
            )

        task.status = CodeGenStatus.GENERATING
        self._save_task(task)

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
            return self._save_task(task)

        task.status = CodeGenStatus.LINTING
        self._save_task(task)

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
        return self._save_task(task)

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

        task = self._save_task(task)
        self._create_review_item(task, reviewer_notes)
        return task

    def _create_review_item(self, task: CodeGenTask, notes: Optional[str]) -> None:
        from .hitl_service import hitl_service
        from ..models.review import ReviewItemCreate, ReviewItemType, ReviewPriority

        requirement = self._requirement_service.get(task.requirement_id) if self._requirement_service else None
        if not requirement:
            return

        hitl_service.create_review_item(
            item_type=ReviewItemType.CODE,
            item_id=task.id,
            data=ReviewItemCreate(
                title=f"代码审核：{requirement.title}"[:200],
                description=(notes or "代码生成已完成，等待审核。")[:5000],
                item_type=ReviewItemType.CODE,
                item_id=task.id,
                project_id=requirement.project_id,
                priority=ReviewPriority.MEDIUM,
            ),
        )

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
