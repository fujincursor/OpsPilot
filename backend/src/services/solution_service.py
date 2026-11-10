"""方案管理服务"""

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
)
from .agents.bugfix_agent import bugfix_agent_service
from .agents.feature_agent import feature_agent_service

if TYPE_CHECKING:
    from .requirement_service import RequirementService
    from .knowledge_service import KnowledgeService


class SolutionService:
    """方案管理服务

    负责方案的 CRUD 操作，以及调用对应的 Agent 生成方案。
    当前使用内存存储，后续可替换为数据库实现。
    """

    def __init__(self):
        self._solutions: Dict[UUID, Union[Solution, BugFixSolution, FeatureDesignSolution]] = {}
        self._requirement_to_solutions: Dict[UUID, List[UUID]] = {}
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

        existing_solutions = self.get_solutions_by_requirement(requirement_id)
        if existing_solutions and not force_regenerate:
            draft_solutions = [
                s for s in existing_solutions
                if s.status == SolutionStatus.DRAFT
            ]
            if draft_solutions:
                return draft_solutions[0]

        if requirement.type == RequirementType.BUG:
            solution = self._generate_bugfix_solution(requirement, additional_context)
        else:
            solution = self._generate_feature_solution(requirement, additional_context)

        self._solutions[solution.id] = solution

        if requirement_id not in self._requirement_to_solutions:
            self._requirement_to_solutions[requirement_id] = []
        self._requirement_to_solutions[requirement_id].append(solution.id)

        self._update_requirement_status(requirement, RequirementStatus.DESIGNING)

        return solution

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
        return self._solutions.get(solution_id)

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

        solution.status = status
        solution.updated_at = datetime.utcnow()

        if reviewed_by:
            solution.reviewed_by = reviewed_by

        if review_comment:
            solution.review_comment = review_comment

        if status == SolutionStatus.APPROVED:
            requirement = self._requirement_service.get(solution.requirement_id)
            if requirement:
                self._update_requirement_status(requirement, RequirementStatus.CODING)
        elif status == SolutionStatus.IMPLEMENTED:
            requirement = self._requirement_service.get(solution.requirement_id)
            if requirement:
                self._update_requirement_status(requirement, RequirementStatus.TESTING)

        return solution

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

        old_solution.status = SolutionStatus.REJECTED
        old_solution.review_comment = "已重新生成新方案"
        old_solution.updated_at = datetime.utcnow()

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
