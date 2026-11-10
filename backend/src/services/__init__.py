"""服务层"""

from .project_service import ProjectService, project_service
from .agent_service import AgentService, agent_service
from .user_service import UserService

project_service.set_agent_service(agent_service)
project_service.init_demo_agents()

__all__ = [
    "ProjectService",
    "project_service",
    "AgentService",
    "agent_service",
    "UserService",
]
