"""Agent 配置服务"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..models.agent import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentType
)


class AgentService:
    """Agent 配置管理服务

    当前使用内存存储，后续可替换为数据库实现
    """

    def __init__(self):
        self._agents: Dict[UUID, AgentConfig] = {}
        self._project_agents: Dict[UUID, List[UUID]] = {}

    def get_agents_by_project(self, project_id: UUID) -> List[AgentConfig]:
        """获取项目的所有 Agent 配置"""
        agent_ids = self._project_agents.get(project_id, [])
        agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
        agents.sort(key=lambda x: x.created_at)
        return agents

    def get_agent(self, agent_id: UUID) -> Optional[AgentConfig]:
        """获取单个 Agent 配置"""
        return self._agents.get(agent_id)

    def create_agent(
        self,
        project_id: UUID,
        data: AgentConfigCreate
    ) -> AgentConfig:
        """创建 Agent 配置"""
        agent = AgentConfig(
            project_id=project_id,
            name=data.name,
            agent_type=data.agent_type,
            description=data.description,
            model_name=data.model_name or "gpt-4",
            temperature=data.temperature if data.temperature is not None else 0.7,
            max_tokens=data.max_tokens or 4096,
            skills=data.skills or [],
            enabled=data.enabled if data.enabled is not None else True
        )

        self._agents[agent.id] = agent

        if project_id not in self._project_agents:
            self._project_agents[project_id] = []
        self._project_agents[project_id].append(agent.id)

        return agent

    def update_agent(
        self,
        agent_id: UUID,
        data: AgentConfigUpdate
    ) -> Optional[AgentConfig]:
        """更新 Agent 配置"""
        agent = self._agents.get(agent_id)
        if not agent:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        agent.updated_at = datetime.utcnow()
        return agent

    def delete_agent(self, agent_id: UUID) -> bool:
        """删除 Agent 配置"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        project_id = agent.project_id
        if project_id in self._project_agents:
            self._project_agents[project_id] = [
                aid for aid in self._project_agents[project_id]
                if aid != agent_id
            ]

        del self._agents[agent_id]
        return True

    def delete_agents_by_project(self, project_id: UUID) -> int:
        """删除项目的所有 Agent 配置"""
        agent_ids = self._project_agents.get(project_id, [])
        count = 0
        for agent_id in agent_ids:
            if agent_id in self._agents:
                del self._agents[agent_id]
                count += 1

        if project_id in self._project_agents:
            del self._project_agents[project_id]

        return count

    def initialize_default_agents(self, project_id: UUID) -> List[AgentConfig]:
        """为新项目初始化默认 Agent 配置"""
        default_agents = [
            AgentConfigCreate(
                name="Lead Agent",
                agent_type=AgentType.LEAD,
                description="主控 Agent，负责任务分解、协调和监督整个运维流程",
                model_name="gpt-4",
                temperature=0.3,
                max_tokens=8192,
                skills=["task_planning", "coordination", "decision_making"],
                enabled=True
            ),
            AgentConfigCreate(
                name="BugFix Agent",
                agent_type=AgentType.BUG_FIX,
                description="Bug 修复专家，负责分析和修复代码缺陷",
                model_name="gpt-4",
                temperature=0.2,
                max_tokens=4096,
                skills=["code_analysis", "debugging", "patch_generation"],
                enabled=True
            ),
            AgentConfigCreate(
                name="Feature Design Agent",
                agent_type=AgentType.FEATURE_DESIGN,
                description="功能设计专家，负责需求分析和方案设计",
                model_name="gpt-4",
                temperature=0.5,
                max_tokens=8192,
                skills=["requirement_analysis", "architecture_design", "documentation"],
                enabled=True
            ),
            AgentConfigCreate(
                name="CodeGen Agent",
                agent_type=AgentType.CODE_GENERATION,
                description="代码生成专家，负责编写和优化代码",
                model_name="gpt-4",
                temperature=0.2,
                max_tokens=4096,
                skills=["code_generation", "refactoring", "optimization"],
                enabled=True
            ),
            AgentConfigCreate(
                name="Test Agent",
                agent_type=AgentType.TEST_EXECUTION,
                description="测试执行专家，负责测试用例生成和执行",
                model_name="gpt-4",
                temperature=0.1,
                max_tokens=4096,
                skills=["test_generation", "test_execution", "coverage_analysis"],
                enabled=True
            ),
        ]

        created_agents = []
        for agent_data in default_agents:
            agent = self.create_agent(project_id, agent_data)
            created_agents.append(agent)

        return created_agents


agent_service = AgentService()
