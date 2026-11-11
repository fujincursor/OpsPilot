"""方案管理服务"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Union, TYPE_CHECKING
from uuid import UUID

from ..models.requirement import Requirement, RequirementType, RequirementStatus
from ..models.solution import (
    Solution,
    BugFixSolution,
    FeatureDesignSolution,
    SolutionType,
    SolutionStatus,
    SolutionUpdate,
    SolutionFilters,
    ImpactAnalysis,
    ImpactLevel,
)
from ..db import DocumentDict
from .agents.bugfix_agent import bugfix_agent_service
from .agents.feature_agent import feature_agent_service

if TYPE_CHECKING:
    from .requirement_service import RequirementService
    from .knowledge_service import KnowledgeService


_SECTION_HEADING = re.compile(r"^(#{2,4})\s+(.+?)\s*$", re.MULTILINE)
_STEP_LINE = re.compile(r"^(?:[-*]|\d+[.)、])\s+(.+?)\s*$", re.MULTILINE)


def _section_body(text: str, keywords: tuple[str, ...]) -> str:
    """取出标题里包含指定词的那一节正文。"""
    matches = list(_SECTION_HEADING.finditer(text or ""))
    for index, match in enumerate(matches):
        title = re.sub(r"^\d+[.、]\s*", "", match.group(2)).strip()
        if not any(word in title for word in keywords):
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return text[match.end():end].strip()
    return ""


def _step_lines(section: str) -> List[str]:
    steps: List[str] = []
    for match in _STEP_LINE.finditer(section or ""):
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", match.group(1)).strip()
        if line and line not in steps:
            steps.append(line)
    return steps


def bugfix_details_from_content(content: str) -> tuple[str, List[str]]:
    """从方案正文中取出这条需求自己的根因和修复步骤。"""
    root = _section_body(content, ("根因",))
    steps = _step_lines(_section_body(content, ("修复步骤", "修改建议", "修改点")))
    return root, steps


def _plain(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text or "").strip()


def _after_colon(line: str) -> str:
    parts = re.split(r"[：:]", line, maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else line.strip()


def _impact_level(text: str) -> ImpactLevel:
    if any(word in text for word in ("高风险", "严重", "核心逻辑")):
        return ImpactLevel.HIGH
    if any(word in text for word in ("中风险", "可能影响", "稳定性")):
        return ImpactLevel.MEDIUM
    return ImpactLevel.LOW


def bugfix_assessment_from_content(content: str) -> tuple[Optional[ImpactAnalysis], str]:
    """从方案正文中取出这条需求自己的影响分析和回归风险。"""
    section = _section_body(content, ("影响范围", "影响分析"))
    bullets = _step_lines(section)
    if not section and not bullets:
        return None, ""

    scope_parts: List[str] = []
    risk_points: List[str] = []
    modules: List[str] = []
    regression = ""
    for line in bullets or [_plain(section)]:
        body = _after_colon(line)
        if "回归风险" in line[:8] or line.startswith("回归"):
            regression = body
            continue
        if "功能影响" in line[:8] or line.startswith("功能"):
            scope_parts.append(body)
        else:
            risk_points.append(body)
        for match in re.finditer(r"(?<!不)影响\s*([^，。；的]+)", body):
            name = match.group(1).strip()
            if name and name not in modules and "不" not in name:
                modules.append(name)

    plain_scope = "；".join(scope_parts) if scope_parts else _plain(section)
    level = _impact_level(plain_scope)
    scope = section.strip() or plain_scope
    impact = ImpactAnalysis(
        level=level,
        scope=scope,
        affected_modules=modules,
        risk_points=risk_points,
    )
    if not regression:
        return impact, ""
    risk_level = _impact_level(regression)
    prefix = {ImpactLevel.HIGH: "高风险", ImpactLevel.MEDIUM: "中风险"}.get(risk_level, "低风险")
    return impact, f"{prefix}: {regression}"


def _model_failure_text(exc: BaseException) -> str:
    text = str(exc)
    if "Recursion limit" in text or "GRAPH_RECURSION_LIMIT" in text:
        return "模型反复调用网页抓取，Jina 连接超时后达到递归上限。已保留本地草稿，页面可以继续刷新。"
    if "ConnectTimeout" in text or "Jina" in text:
        return "Jina 页面抓取连接超时。已保留本地草稿，页面可以继续刷新。"
    return (text.strip() or "模型没有生成方案")[:1000]


def _assigned_skill(project_id: UUID, agent_type) -> tuple[str, str]:
    from .agent_runtime import PRIMARY_SKILL
    from .project_service import project_service

    key = PRIMARY_SKILL.get(agent_type, "")
    project = project_service.get(project_id)
    skill = next((item for item in project.skills if item.key == key), None) if project else None
    return key, (skill.name if skill and skill.name else key)


class SolutionService:
    """方案管理服务

    负责方案的 CRUD 操作，以及调用对应的 Agent 生成方案。
    方案数据保存在数据库中。
    """

    def __init__(self):
        self._solutions: Dict[UUID, Union[Solution, BugFixSolution, FeatureDesignSolution]] = DocumentDict(
            "solutions",
            model=Solution,
            loader=self._load_solution,
        )
        self._requirement_to_solutions: Dict[UUID, List[UUID]] = {}
        for solution in self._solutions.values():
            self._requirement_to_solutions.setdefault(solution.requirement_id, []).append(solution.id)

    @staticmethod
    def _load_solution(payload: dict) -> Union[Solution, BugFixSolution, FeatureDesignSolution]:
        kind = payload.get("type")
        if kind == SolutionType.BUGFIX.value:
            return BugFixSolution.model_validate(payload)
        if kind == SolutionType.FEATURE_DESIGN.value:
            return FeatureDesignSolution.model_validate(payload)
        return Solution.model_validate(payload)
        self._requirement_service: Optional["RequirementService"] = None
        self._knowledge_service: Optional["KnowledgeService"] = None

    def set_requirement_service(self, requirement_service: "RequirementService"):
        """设置需求服务引用"""
        self._requirement_service = requirement_service

    def set_knowledge_service(self, knowledge_service: "KnowledgeService"):
        """设置知识库服务引用"""
        self._knowledge_service = knowledge_service

    def generate_solution(
        self,
        requirement_id: UUID,
        force_regenerate: bool = False,
        additional_context: Optional[str] = None,
    ) -> Optional[Union[BugFixSolution, FeatureDesignSolution]]:
        """根据需求类型调用对应 Agent 生成方案

        Args:
            requirement_id: 需求 ID
            force_regenerate: 是否强制重新生成
            additional_context: 额外上下文信息

        Returns:
            生成的方案，需求不存在返回 None
        """
        if not self._requirement_service:
            raise RuntimeError("RequirementService not set")

        requirement = self._requirement_service.get(requirement_id)
        if not requirement:
            return None
        if requirement.type == RequirementType.QUESTION:
            return None

        existing_solutions = self._solutions_for(requirement_id)
        if not force_regenerate:
            pending_solutions = [
                item for item in existing_solutions
                if item.status == SolutionStatus.PENDING_REVIEW
            ]
            if pending_solutions:
                return pending_solutions[0]
            draft_solutions = [
                item for item in existing_solutions
                if item.status == SolutionStatus.DRAFT
            ]
            if draft_solutions:
                return draft_solutions[0]

        from ..models.agent import AgentType
        from .agent_runtime import agent_runtime

        agent_type = AgentType.BUG_FIX if requirement.type == RequirementType.BUG else AgentType.FEATURE_DESIGN
        agent = agent_runtime.require(requirement.project_id, agent_type)
        if requirement.type == RequirementType.BUG:
            solution = self._generate_bugfix_solution(requirement, additional_context)
        else:
            solution = self._generate_feature_solution(requirement, additional_context)
        model_error = ""
        knowledge_text = self._knowledge_for_prompt(requirement, additional_context)
        try:
            rewritten = agent_runtime.advise(
                agent,
                "请按你的提示词，只针对下面这一条需求写出完整方案。"
                "不要沿用草稿里的通用步骤，除非它确实能解释这一条需求。"
                "方案里要写出这条需求自己的原因、修改点、影响范围、回归风险和验证方法。"
                "如果下面的代码文档和这条需求对应，修改点要写到文档里的文件和函数。\n\n"
                f"需求标题：{requirement.title}\n需求描述：{requirement.description}\n\n"
                f"相关代码文档：\n{knowledge_text or '无'}\n\n草稿：\n{solution.content}",
            )
        except RuntimeError as exc:
            model_error = _model_failure_text(exc)
            rewritten = ""
        if rewritten:
            solution.content = rewritten
            self._sync_bugfix_sections(solution)
        solution.created_by_agent = agent.name
        solution.skill_key, solution.skill_name = _assigned_skill(requirement.project_id, agent_type)

        self._solutions[solution.id] = solution

        if requirement_id not in self._requirement_to_solutions:
            self._requirement_to_solutions[requirement_id] = []
        self._requirement_to_solutions[requirement_id].append(solution.id)

        self._update_requirement_status(requirement, RequirementStatus.DESIGNING)
        if self._requirement_service:
            self._requirement_service.set_failure_reason(requirement.id, model_error or None)

        return solution

    def _knowledge_for_prompt(
        self,
        requirement: Requirement,
        additional_context: Optional[str] = None,
    ) -> str:
        """取出和这条需求最接近的代码说明，交给模型写修改点。"""
        if not self._knowledge_service:
            return ""
        query = f"{requirement.title} {requirement.description or ''}"
        if additional_context:
            query += f" {additional_context}"
        try:
            hits = self._knowledge_service.search_knowledge(
                project_id=requirement.project_id,
                query=query,
                top_k=5,
                snippet_chars=800,
            )
        except Exception:
            return ""
        parts = []
        for hit in hits:
            parts.append(f"- {hit.title}\n{hit.content_snippet}")
        return "\n\n".join(parts)

    def _generate_bugfix_solution(
        self,
        requirement: Requirement,
        additional_context: Optional[str] = None,
    ) -> BugFixSolution:
        """生成 Bug 修复方案"""
        knowledge_results = None
        if self._knowledge_service:
            query = f"{requirement.title} {requirement.description}"
            if additional_context:
                query += f" {additional_context}"

            try:
                knowledge_results = self._knowledge_service.search_knowledge(
                    project_id=requirement.project_id,
                    query=query,
                    top_k=5,
                )
            except Exception:
                pass

        solution = bugfix_agent_service.generate_fix_solution(requirement)

        if knowledge_results:
            root_cause_with_knowledge = bugfix_agent_service.find_root_cause(
                requirement, knowledge_results
            )
            solution.root_cause = root_cause_with_knowledge

        return solution

    def _generate_feature_solution(
        self,
        requirement: Requirement,
        additional_context: Optional[str] = None,
    ) -> FeatureDesignSolution:
        """生成功能设计方案"""
        solution = feature_agent_service.generate_design_doc(requirement)
        return solution

    def _update_requirement_status(
        self, requirement: Requirement, status: RequirementStatus
    ):
        """更新需求状态"""
        if self._requirement_service:
            self._requirement_service.update_status(requirement.id, status)

    def get_solutions_by_requirement(
        self,
        requirement_id: UUID,
        filters: Optional[SolutionFilters] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """获取需求的方案列表

        Args:
            requirement_id: 需求 ID
            filters: 过滤条件
            page: 页码
            page_size: 每页数量

        Returns:
            方案列表
        """
        self.collapse_pending_solutions()
        self.align_with_requirement(requirement_id)
        solution_ids = self._requirement_to_solutions.get(requirement_id, [])
        solutions = [
            self._solutions[sid] for sid in solution_ids
            if sid in self._solutions
        ]

        if filters:
            if filters.type:
                solutions = [s for s in solutions if s.type == filters.type]
            if filters.status:
                solutions = [s for s in solutions if s.status == filters.status]
            if filters.created_by_agent:
                solutions = [
                    s for s in solutions
                    if s.created_by_agent == filters.created_by_agent
                ]

        solutions.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return solutions[start:end]

    def count_solutions_by_requirement(
        self,
        requirement_id: UUID,
        filters: Optional[SolutionFilters] = None,
    ) -> int:
        """统计需求的方案数量"""
        solution_ids = self._requirement_to_solutions.get(requirement_id, [])
        solutions = [
            self._solutions[sid] for sid in solution_ids
            if sid in self._solutions
        ]

        if filters:
            if filters.type:
                solutions = [s for s in solutions if s.type == filters.type]
            if filters.status:
                solutions = [s for s in solutions if s.status == filters.status]
            if filters.created_by_agent:
                solutions = [
                    s for s in solutions
                    if s.created_by_agent == filters.created_by_agent
                ]

        return len(solutions)

    def get_solution(
        self, solution_id: UUID
    ) -> Optional[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """获取单个方案

        Args:
            solution_id: 方案 ID

        Returns:
            方案对象，不存在返回 None
        """
        solution = self._solutions.get(solution_id)
        if solution is None:
            return None
        return self._sync_bugfix_sections(solution)

    def _sync_bugfix_sections(self, solution):
        """用正文里的根因和修改点替换通用模板。"""
        if getattr(solution, "type", None) != SolutionType.BUGFIX:
            return solution
        content = solution.content or ""
        root, steps = bugfix_details_from_content(content)
        impact, regression = bugfix_assessment_from_content(content)
        changed = False
        if root and root != (solution.root_cause or "").strip():
            solution.root_cause = root
            changed = True
        if steps and steps != list(solution.fix_steps or []):
            solution.fix_steps = steps
            changed = True
        if impact is not None and impact.model_dump() != solution.impact_analysis.model_dump():
            solution.impact_analysis = impact
            changed = True
        if regression and regression != (solution.regression_risk or "").strip():
            solution.regression_risk = regression
            changed = True
        if changed:
            solution.updated_at = datetime.utcnow()
            self._solutions[solution.id] = solution
        return solution

    def update_solution(
        self,
        solution_id: UUID,
        data: SolutionUpdate,
    ) -> Optional[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """更新方案

        Args:
            solution_id: 方案 ID
            data: 更新数据

        Returns:
            更新后的方案，不存在返回 None
        """
        solution = self._solutions.get(solution_id)
        if not solution:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(solution, field):
                setattr(solution, field, value)

        solution.updated_at = datetime.utcnow()
        return solution

    def update_solution_status(
        self,
        solution_id: UUID,
        status: SolutionStatus,
        reviewed_by: Optional[str] = None,
        review_comment: Optional[str] = None,
    ) -> Optional[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """更新方案状态

        Args:
            solution_id: 方案 ID
            status: 新状态
            reviewed_by: 审核人
            review_comment: 审核意见

        Returns:
            更新后的方案，不存在返回 None
        """
        solution = self._solutions.get(solution_id)
        if not solution:
            return None

        previous = solution.status
        solution.status = status
        solution.updated_at = datetime.utcnow()

        if reviewed_by:
            solution.reviewed_by = reviewed_by

        if review_comment:
            solution.review_comment = review_comment

        self._solutions[solution.id] = solution
        if status == SolutionStatus.DRAFT and previous == SolutionStatus.PENDING_REVIEW:
            self._supersede_open_review(solution, "方案已撤回待审核")
            self._release_requirement_if_idle(solution)

        if status == SolutionStatus.APPROVED:
            requirement = self._requirement_service.get(solution.requirement_id)
            if requirement:
                self._update_requirement_status(requirement, RequirementStatus.CODING)
        elif status == SolutionStatus.IMPLEMENTED:
            requirement = self._requirement_service.get(solution.requirement_id)
            if requirement:
                self._update_requirement_status(requirement, RequirementStatus.TESTING)

        return solution

    def has_pending_solution(self, requirement_id: UUID) -> bool:
        return any(
            item.status == SolutionStatus.PENDING_REVIEW
            for item in self._solutions_for(requirement_id)
        )

    def collapse_pending_solutions(self) -> None:
        """同一条需求只保留最新一份待审核方案，其余作废。"""
        grouped: Dict[UUID, List[Union[Solution, BugFixSolution, FeatureDesignSolution]]] = {}
        for solution in self._solutions.values():
            if solution.status != SolutionStatus.PENDING_REVIEW:
                continue
            grouped.setdefault(solution.requirement_id, []).append(solution)
        for items in grouped.values():
            items.sort(key=lambda item: item.created_at)
            for stale in items[:-1]:
                self._void_solution(stale, "同一需求只保留最新的待审核方案，此方案作废")

    def _solutions_for(self, requirement_id: UUID):
        return [
            self._solutions[solution_id]
            for solution_id in self._requirement_to_solutions.get(requirement_id, [])
            if solution_id in self._solutions
        ]

    def _void_solution(self, solution, reason: str) -> None:
        from ..models.review import ReviewItemType, ReviewStatus
        from .hitl_service import hitl_service

        solution.status = SolutionStatus.REJECTED
        solution.review_comment = reason
        solution.updated_at = datetime.utcnow()
        self._solutions[solution.id] = solution
        review = hitl_service.find_by_item(ReviewItemType.SOLUTION, solution.id)
        if review is not None and review.status in {ReviewStatus.PENDING, ReviewStatus.IN_REVIEW}:
            hitl_service.supersede(review.id, reason)

    def align_with_requirement(self, requirement_id: UUID) -> None:
        """需求还在设计阶段时，待审核方案退回草稿，审核项一并撤回。"""
        if not self._requirement_service:
            return
        requirement = self._requirement_service.get(requirement_id)
        if requirement is None or requirement.status not in {
            RequirementStatus.PENDING,
            RequirementStatus.ANALYZING,
            RequirementStatus.DESIGNING,
        }:
            return
        for solution in self._solutions_for(requirement_id):
            if solution.status == SolutionStatus.PENDING_REVIEW:
                self._withdraw_solution(solution, "需求已退回设计中，方案撤回待审核")

    def _withdraw_solution(self, solution, reason: str) -> None:
        solution.status = SolutionStatus.DRAFT
        solution.review_comment = reason
        solution.updated_at = datetime.utcnow()
        self._solutions[solution.id] = solution
        self._supersede_open_review(solution, reason)

    def _supersede_open_review(self, solution, reason: str) -> None:
        from ..models.review import ReviewItemType, ReviewStatus
        from .hitl_service import hitl_service

        review = hitl_service.find_by_item(ReviewItemType.SOLUTION, solution.id)
        if review is not None and review.status in {ReviewStatus.PENDING, ReviewStatus.IN_REVIEW}:
            hitl_service.supersede(review.id, reason)

    def _release_requirement_if_idle(self, solution) -> None:
        """没有其他待审项时，需求从审核中回到设计中。"""
        from ..models.review import ReviewStatus
        from .hitl_service import hitl_service

        if not self._requirement_service or self.has_pending_solution(solution.requirement_id):
            return
        requirement = self._requirement_service.get(solution.requirement_id)
        if requirement is None or requirement.status != RequirementStatus.REVIEWING:
            return
        still_open = any(
            item.requirement_id == requirement.id and item.status in {ReviewStatus.PENDING, ReviewStatus.IN_REVIEW}
            for item in hitl_service._review_items.values()
        )
        if still_open:
            return
        self._update_requirement_status(requirement, RequirementStatus.DESIGNING)

    def regenerate_solution(
        self,
        solution_id: UUID,
        additional_context: Optional[str] = None,
    ) -> Optional[Union[BugFixSolution, FeatureDesignSolution]]:
        """重新生成方案

        Args:
            solution_id: 原方案 ID
            additional_context: 额外上下文

        Returns:
            新生成的方案
        """
        old_solution = self._solutions.get(solution_id)
        if not old_solution:
            return None

        reason = "已重新生成，之前的方案作废"
        for solution in self._solutions_for(old_solution.requirement_id):
            if solution.status == SolutionStatus.IMPLEMENTED:
                continue
            if solution.id != old_solution.id and solution.status not in {
                SolutionStatus.DRAFT,
                SolutionStatus.PENDING_REVIEW,
            }:
                continue
            if solution.status == SolutionStatus.REJECTED:
                continue
            self._void_solution(solution, reason)

        return self.generate_solution(
            requirement_id=old_solution.requirement_id,
            force_regenerate=True,
            additional_context=additional_context,
        )

    def delete_solution(self, solution_id: UUID) -> bool:
        """删除方案

        Args:
            solution_id: 方案 ID

        Returns:
            是否删除成功
        """
        solution = self._solutions.get(solution_id)
        if not solution:
            return False

        requirement_id = solution.requirement_id
        if requirement_id in self._requirement_to_solutions:
            self._requirement_to_solutions[requirement_id] = [
                sid for sid in self._requirement_to_solutions[requirement_id]
                if sid != solution_id
            ]

        del self._solutions[solution_id]
        return True

    def delete_solutions_by_requirement(self, requirement_id: UUID) -> int:
        """删除需求下所有方案

        Args:
            requirement_id: 需求 ID

        Returns:
            删除的方案数量
        """
        solution_ids = self._requirement_to_solutions.get(requirement_id, [])
        count = 0

        for solution_id in solution_ids:
            if solution_id in self._solutions:
                del self._solutions[solution_id]
                count += 1

        if requirement_id in self._requirement_to_solutions:
            del self._requirement_to_solutions[requirement_id]

        return count

    def get_solution_statistics(self, requirement_id: Optional[UUID] = None) -> dict:
        """获取方案统计

        Args:
            requirement_id: 需求 ID（可选，不传则统计全部）

        Returns:
            统计数据
        """
        if requirement_id:
            solution_ids = self._requirement_to_solutions.get(requirement_id, [])
            solutions = [
                self._solutions[sid] for sid in solution_ids
                if sid in self._solutions
            ]
        else:
            solutions = list(self._solutions.values())

        by_type = {}
        for t in SolutionType:
            by_type[t.value] = len([s for s in solutions if s.type == t])

        by_status = {}
        for s in SolutionStatus:
            by_status[s.value] = len([sol for sol in solutions if sol.status == s])

        by_agent = {}
        for sol in solutions:
            agent = sol.created_by_agent or "unknown"
            by_agent[agent] = by_agent.get(agent, 0) + 1

        return {
            "total": len(solutions),
            "by_type": by_type,
            "by_status": by_status,
            "by_agent": by_agent,
        }


solution_service = SolutionService()
