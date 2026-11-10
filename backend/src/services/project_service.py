"""项目服务"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..models.project import Project, ProjectCreate, ProjectUpdate, ProjectStatus


class ProjectService:
    """项目管理服务

    当前使用内存存储，后续可替换为数据库实现
    """

    def __init__(self):
        self._projects: Dict[UUID, Project] = {}
        self._init_demo_data()

    def _init_demo_data(self):
        """初始化演示数据"""
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
            self.create(project_data)

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

    def create(self, data: ProjectCreate) -> Project:
        """创建项目"""
        project = Project(**data.model_dump())
        self._projects[project.id] = project
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
        return project

    def delete(self, project_id: UUID) -> bool:
        """删除项目"""
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False


project_service = ProjectService()
