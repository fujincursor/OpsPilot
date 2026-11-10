"""项目服务"""

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from ..db import DocumentDict
from ..models.project import Project, ProjectCreate, ProjectUpdate, ProjectStatus

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

    def _init_demo_data(self):
        """初始化演示数据（不初始化 Agent，稍后由服务注入后初始化）"""
        demo_projects = [
            ProjectCreate(
                name="OpsPilot Demo",
                description="运维领航演示项目",
                repo_url="https://github.com/example/opspilot-demo"
            ),
            ProjectCreate(
                name="微服务监控平台",
                description="用于监控微服务架构的运维平台",
                repo_url="https://github.com/example/microservice-monitor"
            ),
        ]
        for project_data in demo_projects:
            self.create(project_data, init_agents=False)

    def init_demo_agents(self):
        """为演示项目初始化 Agent 配置（在 agent_service 注入后调用）"""
        if self._agent_service:
            for project_id in self._projects.keys():
                if not self._agent_service.get_agents_by_project(project_id):
                    self._agent_service.initialize_default_agents(project_id)

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
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.utcnow()
        self._projects[project.id] = project
        return project

    def delete(self, project_id: UUID) -> bool:
        """删除项目及其相关 Agent 配置"""
        if project_id in self._projects:
            if self._agent_service:
                self._agent_service.delete_agents_by_project(project_id)
            del self._projects[project_id]
            return True
        return False


project_service = ProjectService()
