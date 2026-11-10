"""需求主流程推进。

方案审批通过后生成代码，代码审批通过后执行测试，测试通过后回写知识。
咨询不进入编码。驳回修订回到上一阶段，拒绝则关闭需求。
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from ..models.knowledge import KnowledgeReadyStatus
from ..models.requirement import Requirement, RequirementStatus, RequirementType
from ..models.review import ReviewItem, ReviewItemCreate, ReviewItemType, ReviewPriority, ReviewStatus
from ..models.solution import SolutionStatus

logger = logging.getLogger(__name__)

COVERAGE_GATE = 80.0


class WorkflowService:
    """把审核决定接到下一阶段。"""

    def knowledge_block(self, project_id: UUID) -> Optional[KnowledgeReadyStatus]:
        """知识库或项目资料未就绪时返回状态，都就绪则返回 None。"""
        from .knowledge_service import knowledge_service
        from .project_service import project_service

        status = knowledge_service.check_knowledge_ready(project_id)
        profile_message = self._profile_gap(project_service.get(project_id))
        if status.is_ready and not profile_message:
            return None
        parts = []
        if not status.is_ready:
            parts.append(status.message or "知识库尚未就绪")
        if profile_message:
            parts.append(profile_message)
        status.is_ready = False
        status.message = "；".join(parts)
        return status

    def _profile_gap(self, project) -> str:
        if project is None:
            return "项目不存在"
        profile = getattr(project, "profile", None)
        overview = self._profile_text(profile, "overview") or (project.description or "")
        architecture = self._profile_text(profile, "architecture")
        directory = self._profile_text(profile, "directory_layout")
        if overview and (architecture or directory):
            return ""
        return "请先补齐项目概述，以及架构说明或目录结构"

    @staticmethod
    def _profile_text(profile, name: str) -> str:
        if profile is None:
            return ""
        if isinstance(profile, dict):
            return str(profile.get(name) or "").strip()
        return str(getattr(profile, name, "") or "").strip()

    async def open_solution_review(self, requirement: Requirement) -> Optional[ReviewItem]:
        """为 Bug 或新需求生成方案并创建审批。咨询直接返回。"""
        if requirement.type == RequirementType.QUESTION:
            return None
        if not requirement.auto_advance or requirement.status == RequirementStatus.CLOSED:
            return None

        from .requirement_service import requirement_service
        from .solution_service import solution_service

        try:
            requirement_service.update_status(requirement.id, RequirementStatus.DESIGNING)
            solution = solution_service.generate_solution(requirement.id)
        except Exception:
            logger.exception("方案生成失败: %s", requirement.id)
            self._note(requirement, "方案生成失败，流程已停在方案阶段。可以在需求详情中重新生成。", "error")
            return None
        if solution is None:
            return None
        return self._queue_solution_review(solution, requirement)

    async def on_approved(self, review: ReviewItem) -> None:
        """审批通过后进入代码生成或测试。"""
        requirement = self._requirement_for(review)
        if requirement is None or requirement.type == RequirementType.QUESTION:
            return
        self._mark_card(review, "approved")
        if not requirement.auto_advance or requirement.status == RequirementStatus.CLOSED:
            self._note(requirement, "已通过，但自动推进已暂停。恢复后会从当前阶段继续。")
            return
        try:
            if review.item_type == ReviewItemType.SOLUTION:
                await self._after_solution_approved(requirement, review)
            elif review.item_type == ReviewItemType.CODE:
                await self._after_code_approved(requirement, review)
        except Exception:
            logger.exception("流程推进失败: %s", review.id)
            self._note(requirement, "审批已记录，但下一阶段执行失败。可在监控中恢复自动推进后重试。", "error")

    async def on_rejected(self, review: ReviewItem, reason: str) -> None:
        """拒绝会关闭需求，不再进入编码或测试。"""
        from .requirement_service import requirement_service
        from .solution_service import solution_service

        requirement = self._requirement_for(review)
        self._mark_card(review, "rejected")
        if review.item_type == ReviewItemType.SOLUTION:
            solution_service.update_solution_status(
                review.item_id,
                SolutionStatus.REJECTED,
                review_comment=reason,
            )
        if requirement is not None:
            requirement_service.update_status(requirement.id, RequirementStatus.CLOSED)
            self._note(requirement, f"审批已拒绝，需求关闭。原因：{reason}")

    async def on_revision(self, review: ReviewItem, comments: str) -> None:
        """要求修改时带着意见回到方案或代码生成。"""
        requirement = self._requirement_for(review)
        if requirement is None or not requirement.auto_advance:
            self._mark_card(review, "revision_requested")
            return
        self._mark_card(review, "revision_requested")
        try:
            if review.item_type == ReviewItemType.SOLUTION:
                await self._revise_solution(requirement, review, comments)
            elif review.item_type == ReviewItemType.CODE:
                await self._revise_code(requirement, review, comments)
        except Exception:
            logger.exception("驳回重做失败: %s", review.id)
            self._note(requirement, "已记录修改意见，但重新生成失败。", "error")

    def pause(self, requirement_id: UUID) -> Optional[Requirement]:
        from .requirement_service import requirement_service

        return requirement_service.set_auto_advance(requirement_id, False)

    def stop(self, requirement_id: UUID) -> Optional[Requirement]:
        from .requirement_service import requirement_service

        requirement = requirement_service.update_status(requirement_id, RequirementStatus.CLOSED)
        if requirement is None:
            return None
        return requirement_service.set_auto_advance(requirement_id, False)

    async def resume(self, requirement_id: UUID) -> Optional[Requirement]:
        """恢复自动推进。没有待审项时，从已经通过的阶段继续。"""
        from .requirement_service import requirement_service

        requirement = requirement_service.set_auto_advance(requirement_id, True)
        if requirement is None or requirement.status in {
            RequirementStatus.CLOSED,
            RequirementStatus.COMPLETED,
        } or requirement.type == RequirementType.QUESTION:
            return requirement
        await self._continue(requirement)
        return requirement_service.get(requirement_id)

    async def _continue(self, requirement: Requirement) -> None:
        from .codegen_service import codegen_service
        from .hitl_service import hitl_service
        from .test_service import test_service

        reviews = [
            item for item in hitl_service._review_items.values()
            if item.requirement_id == requirement.id
        ]
        if any(item.status in {ReviewStatus.PENDING, ReviewStatus.IN_REVIEW} for item in reviews):
            return
        approved_code = [
            item for item in reviews
            if item.item_type == ReviewItemType.CODE and item.status == ReviewStatus.APPROVED
        ]
        if approved_code:
            review = max(approved_code, key=lambda item: item.updated_at)
            tests = test_service.get_tasks_by_codegen(review.item_id)
            passed = [
                task for task in tests
                if task.status.value == "completed" and not self._needs_rework(task.id)
            ]
            if passed:
                if requirement.status != RequirementStatus.COMPLETED:
                    report = test_service.get_test_report(passed[-1].id)
                    task = codegen_service.get_task(review.item_id)
                    if report is not None and task is not None:
                        await self._complete(requirement, task.id, report)
                return
            await self._after_code_approved(requirement, review)
            return
        approved_solution = [
            item for item in reviews
            if item.item_type == ReviewItemType.SOLUTION and item.status == ReviewStatus.APPROVED
        ]
        if approved_solution:
            review = max(approved_solution, key=lambda item: item.updated_at)
            tasks = codegen_service.get_tasks_by_solution(review.item_id)
            if not tasks:
                await self._after_solution_approved(requirement, review)
            return
        if requirement.status in {
            RequirementStatus.PENDING,
            RequirementStatus.ANALYZING,
            RequirementStatus.DESIGNING,
        }:
            await self.open_solution_review(requirement)

    def _needs_rework(self, test_task_id: UUID) -> bool:
        from .test_service import test_service

        report = test_service.get_test_report(test_task_id)
        return report is None or self._test_failed(report)

    def stage_label(self, requirement: Requirement) -> str:
        """给监控页用的阶段名称。"""
        if requirement.status == RequirementStatus.CLOSED:
            return "已关闭"
        if requirement.status == RequirementStatus.COMPLETED:
            return "完成"
        if requirement.status == RequirementStatus.REVIEWING:
            return "待审批"
        if not requirement.auto_advance:
            return "已暂停"
        labels = {
            RequirementStatus.PENDING: "分析",
            RequirementStatus.ANALYZING: "分析",
            RequirementStatus.DESIGNING: "方案",
            RequirementStatus.REVIEWING: "待审批",
            RequirementStatus.CODING: "编码",
            RequirementStatus.TESTING: "测试",
        }
        return labels.get(requirement.status, requirement.status.value)

    async def _after_solution_approved(self, requirement: Requirement, review: ReviewItem) -> None:
        from .requirement_service import requirement_service
        from .solution_service import solution_service

        solution_service.update_solution_status(
            review.item_id,
            SolutionStatus.APPROVED,
            reviewed_by=review.reviewer,
        )
        requirement_service.update_status(requirement.id, RequirementStatus.CODING)
        await self._run_codegen(requirement, review.item_id, None)

    async def _after_code_approved(self, requirement: Requirement, review: ReviewItem) -> None:
        from .codegen_service import codegen_service
        from .requirement_service import requirement_service
        from .test_service import test_service

        task = codegen_service.get_task(review.item_id)
        if task is None or task.status.value != "completed":
            self._note(requirement, "代码任务尚未完成，不能开始测试。", "error")
            return
        code_review = self._approved_code_review(task.id)
        if code_review is None:
            self._note(requirement, "代码还没有审批通过，测试不会开始。")
            return

        requirement_service.update_status(requirement.id, RequirementStatus.TESTING)
        profile = self._sandbox_profile(requirement.project_id)
        test_task = test_service.create_test_task(task.id)
        if test_task is None:
            self._note(requirement, "测试任务创建失败。", "error")
            return
        if profile:
            test_task.sandbox_profile = profile
            test_service._tasks[test_task.id] = test_task
        finished = await test_service.generate_and_run_tests(test_task.id)
        report = test_service.get_test_report(finished.id) if finished else None
        if finished is None or report is None or self._test_failed(report):
            await self._rework_code(requirement, task.id, report)
            return
        await self._complete(requirement, task.id, report)

    async def _run_codegen(
        self,
        requirement: Requirement,
        solution_id: UUID,
        instructions: Optional[str],
    ) -> None:
        from .codegen_service import codegen_service
        from .requirement_service import requirement_service

        requirement_service.update_status(requirement.id, RequirementStatus.CODING)
        task = codegen_service.create_codegen_task(
            solution_id,
            additional_context=instructions,
        )
        if task is None:
            self._note(requirement, "代码任务创建失败。", "error")
            return
        profile = self._sandbox_profile(requirement.project_id)
        if profile:
            task.sandbox_profile = profile
            codegen_service._tasks[task.id] = task
        task = await codegen_service.generate_and_lint(
            task.id,
            additional_instructions=instructions,
        )
        if task is None:
            self._note(requirement, "代码生成失败。", "error")
            return
        if task.lint_result and not task.lint_result.passed:
            task = await codegen_service.regenerate_code(
                task.id,
                fix_lint_errors=True,
                additional_instructions=instructions or "修复语法检查发现的问题",
            )
        if task is None or task.status.value != "completed":
            self._note(requirement, "语法检查后代码仍未完成。", "error")
            return
        self._queue_code_review(requirement, task)

    async def _revise_solution(self, requirement: Requirement, review: ReviewItem, comments: str) -> None:
        from .solution_service import solution_service

        solution = solution_service.regenerate_solution(review.item_id, additional_context=comments)
        if solution is None:
            self._note(requirement, "方案重新生成失败。", "error")
            return
        fresh = self._reload(requirement.id)
        self._queue_solution_review(solution, fresh or requirement)

    async def _revise_code(self, requirement: Requirement, review: ReviewItem, comments: str) -> None:
        from .codegen_service import codegen_service

        task = codegen_service.get_task(review.item_id)
        if task is None:
            return
        await self._run_codegen(requirement, task.solution_id, comments)

    async def _rework_code(self, requirement: Requirement, task_id: UUID, report) -> None:
        from .codegen_service import codegen_service
        from .requirement_service import requirement_service

        current = self._reload(requirement.id) or requirement
        summary = self._failure_summary(report)
        if current.rework_count >= 1:
            current.auto_advance = False
            requirement_service._requirements[current.id] = current
            self._note(current, f"{summary} 已自动回到代码生成一次，这次停下来等待处理。")
            return
        current.rework_count += 1
        requirement_service._requirements[current.id] = current
        task = codegen_service.get_task(task_id)
        if task is None:
            return
        self._note(current, f"{summary} 将带着失败摘要重新生成代码，并再次进入代码审批。")
        await self._run_codegen(current, task.solution_id, summary)

    async def _complete(self, requirement: Requirement, task_id: UUID, report) -> None:
        from .codegen_service import codegen_service
        from .feedback_service import feedback_service
        from .requirement_service import requirement_service
        from .solution_service import solution_service

        solutions = solution_service.get_solutions_by_requirement(requirement.id)
        approved = [item for item in solutions if item.status == SolutionStatus.APPROVED]
        if approved:
            solution_service.update_solution_status(approved[-1].id, SolutionStatus.IMPLEMENTED)
        try:
            codegen_service.create_merge_request(task_id)
        except Exception:
            logger.exception("创建合并请求失败: %s", task_id)
        try:
            feedback_service.create_case_study(requirement.id)
        except Exception:
            logger.exception("知识回写失败: %s", requirement.id)
        requirement_service.update_status(requirement.id, RequirementStatus.COMPLETED)
        passed = getattr(report, "passed", 0)
        total = getattr(report, "total", 0)
        self._note(requirement, f"测试通过（{passed}/{total}）。知识已回写，流程完成。")

    def _queue_solution_review(self, solution, requirement: Requirement) -> ReviewItem:
        from .hitl_service import hitl_service
        from .requirement_service import requirement_service
        from .solution_service import solution_service

        solution_service.update_solution_status(solution.id, SolutionStatus.PENDING_REVIEW)
        requirement_service.update_status(requirement.id, RequirementStatus.REVIEWING)
        summary = (getattr(solution, "content", "") or "")[:800]
        review = hitl_service.create_review_item(
            item_type=ReviewItemType.SOLUTION,
            item_id=solution.id,
            data=ReviewItemCreate(
                title=f"方案审批：{solution.title}"[:200],
                description=summary or "方案已生成，等待审批。",
                item_type=ReviewItemType.SOLUTION,
                item_id=solution.id,
                project_id=requirement.project_id,
                requirement_id=requirement.id,
                session_id=requirement.session_id,
                priority=self._review_priority(requirement),
            ),
        )
        self._publish_card(
            requirement,
            review,
            "方案已经生成，请审批。通过后会自动进入代码生成。",
            summary or solution.title,
            root_cause=str(getattr(solution, "root_cause", "") or ""),
            files=list(getattr(solution, "affected_files", []) or []),
            due_at=review.due_at.isoformat() if review.due_at else None,
        )
        return review

    def _queue_code_review(self, requirement: Requirement, task) -> ReviewItem:
        from .hitl_service import hitl_service
        from .requirement_service import requirement_service

        lint_text = "语法检查已通过。"
        if task.lint_result and not task.lint_result.passed:
            lint_text = f"语法检查仍有 {len(task.lint_result.errors)} 个问题，请在审批时确认。"
        profile = task.sandbox_profile or self._sandbox_profile(requirement.project_id) or "未配置"
        description = f"{lint_text} 执行环境：{profile}"
        requirement_service.update_status(requirement.id, RequirementStatus.REVIEWING)
        review = hitl_service.create_review_item(
            item_type=ReviewItemType.CODE,
            item_id=task.id,
            data=ReviewItemCreate(
                title=f"代码审批：{requirement.title}"[:200],
                description=description,
                item_type=ReviewItemType.CODE,
                item_id=task.id,
                project_id=requirement.project_id,
                requirement_id=requirement.id,
                session_id=requirement.session_id,
                priority=self._review_priority(requirement),
            ),
        )
        files = [getattr(item, "path", "") for item in getattr(task, "files", []) or []]
        self._publish_card(
            requirement,
            review,
            "代码已生成，请审批。通过后会自动执行测试。",
            description,
            files=[item for item in files if item],
            due_at=review.due_at.isoformat() if review.due_at else None,
        )
        return review

    def _publish_card(
        self,
        requirement: Requirement,
        review: ReviewItem,
        content: str,
        summary: str,
        root_cause: str = "",
        files: Optional[list] = None,
        due_at: Optional[str] = None,
    ) -> None:
        if requirement.session_id is None:
            return
        from .chat_service import chat_service

        chat_service.append_review_card(
            requirement.session_id,
            review_id=review.id,
            item_type=review.item_type.value,
            title=review.title,
            summary=summary,
            content=content,
            root_cause=root_cause,
            files=files,
            due_at=due_at,
        )

    def _mark_card(self, review: ReviewItem, status: str) -> None:
        if review.session_id is None:
            return
        from .chat_service import chat_service

        chat_service.mark_review(review.session_id, review.id, status)

    def _note(self, requirement: Requirement, content: str, status: str = "complete") -> None:
        if requirement.session_id is None:
            return
        from .chat_service import chat_service

        chat_service.append_note(requirement.session_id, content, status)

    def _requirement_for(self, review: ReviewItem) -> Optional[Requirement]:
        from .codegen_service import codegen_service
        from .requirement_service import requirement_service
        from .solution_service import solution_service

        if review.requirement_id:
            return requirement_service.get(review.requirement_id)
        if review.item_type == ReviewItemType.SOLUTION:
            solution = solution_service.get_solution(review.item_id)
            if solution:
                return requirement_service.get(solution.requirement_id)
        if review.item_type == ReviewItemType.CODE:
            task = codegen_service.get_task(review.item_id)
            if task:
                return requirement_service.get(task.requirement_id)
        return None

    def _reload(self, requirement_id: UUID) -> Optional[Requirement]:
        from .requirement_service import requirement_service

        return requirement_service.get(requirement_id)

    def _approved_code_review(self, task_id: UUID) -> Optional[ReviewItem]:
        from .hitl_service import hitl_service

        review = hitl_service.find_by_item(ReviewItemType.CODE, task_id)
        if review and review.status == ReviewStatus.APPROVED:
            return review
        return None

    def _sandbox_profile(self, project_id: UUID) -> str:
        from .project_service import project_service

        project = project_service.get(project_id)
        if project is None or project.sandbox is None:
            return ""
        sandbox = project.sandbox
        domains = "、".join(sandbox.allowed_domains) if sandbox.allowed_domains else "无"
        return (
            f"{sandbox.backend} / {sandbox.memory_mb}MB / CPU {sandbox.cpu} / "
            f"超时 {sandbox.timeout_seconds}s / 网络 {sandbox.network_policy} / 白名单 {domains}"
        )

    def _review_priority(self, requirement: Requirement) -> ReviewPriority:
        mapping = {
            "low": ReviewPriority.LOW,
            "medium": ReviewPriority.MEDIUM,
            "high": ReviewPriority.HIGH,
            "critical": ReviewPriority.URGENT,
        }
        value = requirement.priority.value if hasattr(requirement.priority, "value") else str(requirement.priority)
        return mapping.get(value, ReviewPriority.MEDIUM)

    def _test_failed(self, report) -> bool:
        if getattr(report, "failed", 0) > 0:
            return True
        coverage = float(getattr(report, "coverage_percent", 0) or 0)
        return coverage > 0 and coverage < COVERAGE_GATE

    def _failure_summary(self, report) -> str:
        if report is None:
            return "测试没有产生报告。"
        names = "、".join(getattr(report, "failed_cases", [])[:8])
        coverage = getattr(report, "coverage_percent", 0)
        extra = f" 失败用例：{names}。" if names else ""
        return (
            f"测试未过门禁：失败 {getattr(report, 'failed', 0)} 个，"
            f"覆盖率 {coverage}%。{extra}"
        )


workflow_service = WorkflowService()
