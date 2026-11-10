"""服务层"""

from .project_service import ProjectService, project_service
from .agent_service import AgentService, agent_service
from .user_service import UserService
from .knowledge_service import KnowledgeService, knowledge_service

project_service.set_agent_service(agent_service)
project_service.init_demo_agents()

knowledge_service.set_project_service(project_service)
for pid in list(project_service._projects.keys()):
    knowledge_service.init_demo_knowledge(pid)

__all__ = [
    "ProjectService",
    "project_service",
    "AgentService",
    "agent_service",
    "UserService",
    "KnowledgeService",
    "knowledge_service",
]
