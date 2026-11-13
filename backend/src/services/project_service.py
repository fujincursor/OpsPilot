"""项目服务"""

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from ..db import DocumentDict
from ..models.project import Project, ProjectCreate, ProjectSkill, ProjectUpdate, ProjectStatus, default_project_skills
from ..store import list_skill_catalog

if TYPE_CHECKING:
    from .agent_service import AgentService


class ProjectService:
    """项目管理服务。项目数据保存在数据库中。"""

    def __init__(self):
        self._projects: Dict[UUID, Project] = DocumentDict("projects", model=Project)
        self._agent_service: Optional["AgentService"] = None

    def set_agent_service(self, agent_service: "AgentService"):
        """设置 Agent 服务引用（避免循环导入）"""
        self._agent_service = agent_service

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ProjectStatus] = None
    ) -> tuple[List[Project], int]:
        """获取项目列表"""
        projects = list(self._projects.values())

        if status:
            projects = [p for p in projects if p.status == status]

        projects.sort(key=lambda x: x.created_at, reverse=True)

        total = len(projects)
        start = (page - 1) * page_size
        end = start + page_size

        return projects[start:end], total

    def get(self, project_id: UUID) -> Optional[Project]:
        """获取单个项目"""
        return self._projects.get(project_id)

    def create(self, data: ProjectCreate, init_agents: bool = True) -> Project:
        """创建项目

        Args:
            data: 项目创建数据
            init_agents: 是否初始化默认 Agent 配置
        """
        project = Project(**data.model_dump())
        project.skills = self._skills_from_catalog()
        self._projects[project.id] = project

        if init_agents and self._agent_service:
            self._agent_service.initialize_default_agents(project.id)

        return project

    def update(self, project_id: UUID, data: ProjectUpdate) -> Optional[Project]:
        """更新项目"""
        project = self._projects.get(project_id)
        if not project:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "skills" in update_data:
            update_data["skills"] = self._keep_skill_usage(project, update_data["skills"])
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.utcnow()
        self._projects[project.id] = project
        return project

    def record_skill_use(self, project_id: UUID, key: str) -> None:
        """技能参与一次执行后，把项目设置里的使用次数加一。"""
        project = self._projects.get(project_id)
        if project is None or not key:
            return
        matched = False
        for skill in project.skills:
            if skill.key == key:
                skill.usage_count = int(skill.usage_count or 0) + 1
                matched = True
                break
        if not matched:
            return
        project.updated_at = datetime.utcnow()
        self._projects[project.id] = project

    @staticmethod
    def _skills_from_catalog() -> List[ProjectSkill]:
        """新项目的技能开关从技能目录复制。目录为空时使用内置清单。"""
        rows = list_skill_catalog()
        if not rows:
            return default_project_skills()
        return [
            ProjectSkill(
                key=row["key"],
                name=row["name"],
                description=row["description"],
                agent=row["agent"],
            )
            for row in rows
        ]

    @staticmethod
    def _keep_skill_usage(project: Project, incoming) -> list:
        """保存项目设置时保留已经累计的使用次数。"""
        previous = {item.key: int(item.usage_count or 0) for item in project.skills}
        merged = []
        for raw in incoming or []:
            skill = raw if isinstance(raw, ProjectSkill) else ProjectSkill.model_validate(raw)
            skill.usage_count = previous.get(skill.key, int(skill.usage_count or 0))
            merged.append(skill)
        return merged

    def delete(self, project_id: UUID) -> bool:
        """删除项目及其相关 Agent 配置"""
        if project_id in self._projects:
            if self._agent_service:
                self._agent_service.delete_agents_by_project(project_id)
            from .knowledge_service import knowledge_service

            for kb_id in [item.id for item in knowledge_service.get_knowledge_bases(project_id)]:
                knowledge_service.delete_knowledge_base(kb_id)
            from .workspace_service import workspace_service

            workspace_service.remove(project_id)
            del self._projects[project_id]
            return True
        return False


project_service = ProjectService()
