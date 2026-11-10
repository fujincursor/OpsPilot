"""服务层"""

from .project_service import ProjectService, project_service
from .agent_service import AgentService, agent_service
from .user_service import UserService
from .knowledge_service import KnowledgeService, knowledge_service
from .lead_agent_service import LeadAgentService, lead_agent_service
from .requirement_service import RequirementService, requirement_service
from .solution_service import SolutionService, solution_service
from .agents import (
    BugFixAgentService,
    bugfix_agent_service,
    FeatureDesignAgentService,
    feature_agent_service,
)

project_service.set_agent_service(agent_service)
project_service.init_demo_agents()

knowledge_service.set_project_service(project_service)
for pid in list(project_service._projects.keys()):
    knowledge_service.init_demo_knowledge(pid)

requirement_service.set_project_service(project_service)

solution_service.set_requirement_service(requirement_service)
solution_service.set_knowledge_service(knowledge_service)

__all__ = [
    "ProjectService",
    "project_service",
    "AgentService",
    "agent_service",
    "UserService",
    "KnowledgeService",
    "knowledge_service",
    "LeadAgentService",
    "lead_agent_service",
    "RequirementService",
    "requirement_service",
    "SolutionService",
    "solution_service",
    "BugFixAgentService",
    "bugfix_agent_service",
    "FeatureDesignAgentService",
    "feature_agent_service",
]
