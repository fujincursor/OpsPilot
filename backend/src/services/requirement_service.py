"""需求管理服务"""

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from ..models.requirement import (
    Requirement,
    RequirementCreate,
    RequirementUpdate,
    RequirementType,
    RequirementStatus,
    RequirementPriority,
    RequirementFilters,
)
from .lead_agent_service import lead_agent_service

if TYPE_CHECKING:
    from .project_service import ProjectService


class RequirementService:
    """需求管理服务

    负责需求的 CRUD 操作，并集成 Lead Agent 进行智能分析。
    当前使用内存存储，后续可替换为数据库实现。
    """

    def __init__(self):
        self._requirements: Dict[UUID, Requirement] = {}
        self._project_service: Optional["ProjectService"] = None
        self._init_demo_data()

    def set_project_service(self, project_service: "ProjectService"):
        """设置项目服务引用（避免循环导入）"""
        self._project_service = project_service

    def _init_demo_data(self):
        """初始化演示数据"""
        pass

    def create(
        self,
        project_id: UUID,
        data: RequirementCreate,
        created_by: Optional[str] = None
    ) -> Requirement:
        """创建需求

        自动调用 Lead Agent 分析需求文本，提取类型、优先级和关键词。

        Args:
            project_id: 项目 ID
            data: 需求创建数据
            created_by: 创建人

        Returns:
            Requirement: 创建的需求
        """
        full_text = f"{data.title} {data.description}"
        analysis = lead_agent_service.analyze_requirement(full_text)

        req_type = data.type if data.type else analysis.type
        priority = data.priority if data.priority else analysis.priority

        requirement = Requirement(
            project_id=project_id,
            title=data.title,
            description=data.description,
            source=data.source,
            type=req_type,
            priority=priority,
            status=RequirementStatus.PENDING,
            created_by=created_by,
            keywords=analysis.keywords,
            analysis_confidence=analysis.confidence,
        )

        self._requirements[requirement.id] = requirement
        return requirement

    def list(
        self,
        project_id: UUID,
        filters: Optional[RequirementFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Requirement], int]:
        """获取需求列表

        Args:
            project_id: 项目 ID
            filters: 过滤条件
            page: 页码
            page_size: 每页数量

        Returns:
            tuple[List[Requirement], int]: (需求列表, 总数)
        """
        requirements = [
            r for r in self._requirements.values()
            if r.project_id == project_id
        ]

        if filters:
            if filters.type:
                requirements = [r for r in requirements if r.type == filters.type]
            if filters.status:
                requirements = [r for r in requirements if r.status == filters.status]
            if filters.priority:
                requirements = [r for r in requirements if r.priority == filters.priority]
            if filters.assignee:
                requirements = [r for r in requirements if r.assignee == filters.assignee]
            if filters.keyword:
                keyword_lower = filters.keyword.lower()
                requirements = [
                    r for r in requirements
                    if keyword_lower in r.title.lower() or
                       keyword_lower in r.description.lower() or
                       any(keyword_lower in kw.lower() for kw in r.keywords)
                ]

        requirements.sort(key=lambda x: x.created_at, reverse=True)

        total = len(requirements)
        start = (page - 1) * page_size
        end = start + page_size

        return requirements[start:end], total

    def get(self, requirement_id: UUID) -> Optional[Requirement]:
        """获取单个需求

        Args:
            requirement_id: 需求 ID

        Returns:
            Optional[Requirement]: 需求对象，不存在返回 None
        """
        return self._requirements.get(requirement_id)

    def update(
        self,
        requirement_id: UUID,
        data: RequirementUpdate
    ) -> Optional[Requirement]:
        """更新需求

        如果更新了标题或描述，会重新进行 AI 分析。

        Args:
            requirement_id: 需求 ID
            data: 更新数据

        Returns:
            Optional[Requirement]: 更新后的需求，不存在返回 None
        """
        requirement = self._requirements.get(requirement_id)
        if not requirement:
            return None

        update_data = data.model_dump(exclude_unset=True)

        need_reanalyze = "title" in update_data or "description" in update_data

        for field, value in update_data.items():
            setattr(requirement, field, value)

        if need_reanalyze:
            full_text = f"{requirement.title} {requirement.description}"
            analysis = lead_agent_service.analyze_requirement(full_text)
            requirement.keywords = analysis.keywords
            requirement.analysis_confidence = analysis.confidence

            if "type" not in update_data:
                requirement.type = analysis.type
            if "priority" not in update_data:
                requirement.priority = analysis.priority

        requirement.updated_at = datetime.utcnow()
        return requirement

    def update_status(
        self,
        requirement_id: UUID,
        status: RequirementStatus
    ) -> Optional[Requirement]:
        """更新需求状态

        Args:
            requirement_id: 需求 ID
            status: 新状态

        Returns:
            Optional[Requirement]: 更新后的需求，不存在返回 None
        """
        requirement = self._requirements.get(requirement_id)
        if not requirement:
            return None

        requirement.status = status
        requirement.updated_at = datetime.utcnow()
        return requirement

    def assign(
        self,
        requirement_id: UUID,
        assignee: str
    ) -> Optional[Requirement]:
        """分配需求

        Args:
            requirement_id: 需求 ID
            assignee: 分配人

        Returns:
            Optional[Requirement]: 更新后的需求，不存在返回 None
        """
        requirement = self._requirements.get(requirement_id)
        if not requirement:
            return None

        requirement.assignee = assignee
        requirement.updated_at = datetime.utcnow()

        if requirement.status == RequirementStatus.PENDING:
            requirement.status = RequirementStatus.ANALYZING

        return requirement

    def delete(self, requirement_id: UUID) -> bool:
        """删除需求

        Args:
            requirement_id: 需求 ID

        Returns:
            bool: 是否删除成功
        """
        if requirement_id in self._requirements:
            del self._requirements[requirement_id]
            return True
        return False

    def delete_by_project(self, project_id: UUID) -> int:
        """删除项目下所有需求

        Args:
            project_id: 项目 ID

        Returns:
            int: 删除的需求数量
        """
        to_delete = [
            req_id for req_id, req in self._requirements.items()
            if req.project_id == project_id
        ]
        for req_id in to_delete:
            del self._requirements[req_id]
        return len(to_delete)

    def get_statistics(self, project_id: UUID) -> dict:
        """获取项目需求统计

        Args:
            project_id: 项目 ID

        Returns:
            dict: 统计数据
        """
        requirements = [
            r for r in self._requirements.values()
            if r.project_id == project_id
        ]

        by_type = {}
        for t in RequirementType:
            by_type[t.value] = len([r for r in requirements if r.type == t])

        by_status = {}
        for s in RequirementStatus:
            by_status[s.value] = len([r for r in requirements if r.status == s])

        by_priority = {}
        for p in RequirementPriority:
            by_priority[p.value] = len([r for r in requirements if r.priority == p])

        return {
            "total": len(requirements),
            "by_type": by_type,
            "by_status": by_status,
            "by_priority": by_priority,
        }


requirement_service = RequirementService()
