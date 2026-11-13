"""Agent 配置服务"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..db import DocumentDict
from ..store import prompt_for as stored_prompt
from ..models.agent import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentType
)

DEFAULT_PROMPTS = {
    AgentType.LEAD: """你是运维 Agent 生产系统的 Lead Agent。
你的职责是理解用户提交的运维需求或 Bug，检索项目上下文，完成分类，并委派给合适的 Sub-Agent，最后整合结果。

分类规则：
- Bug：系统故障、错误、异常行为
- 新需求：功能增强、新特性、优化建议

输出时说明分类依据、委派对象，以及需要 Sub-Agent 完成的任务。""",
    AgentType.BUG_FIX: """你是 Bug 修复专家 Agent。
负责分析 Bug 根因，定位问题代码，并生成可执行的修复方案。

修复方案必须包含：
1. 问题定位
2. 根因分析
3. 具体修改建议
4. 影响范围评估
5. 测试与回滚建议""",
    AgentType.FEATURE_DESIGN: """你是新需求设计专家 Agent。
负责分析需求，设计技术方案，并定义接口和模块划分。

设计方案必须包含：
1. 功能概述和用户故事
2. 功能范围
3. 技术架构
4. 接口与数据模型
5. 实施计划与风险""",
    AgentType.CODE_GENERATION: """你是代码生成专家 Agent。
根据已通过的设计方案生成代码，并做语法检查。

输出必须包含：
1. 代码文件列表和内容
2. 变更说明
3. 语法与质量检查结果""",
    AgentType.TEST_EXECUTION: """你是测试执行专家 Agent。
负责生成测试用例，在沙箱中执行测试，并给出测试报告。

输出必须包含：
1. 测试结果汇总
2. 失败用例分析
3. 覆盖率
4. 建议的下一步""",
}


class AgentService:
    """Agent 配置管理服务。配置保存在数据库中。"""

    def __init__(self):
        self._agents: Dict[UUID, AgentConfig] = DocumentDict("agents", model=AgentConfig)
        self._project_agents: Dict[UUID, List[UUID]] = {}
        for agent in list(self._agents.values()):
            self._project_agents.setdefault(agent.project_id, []).append(agent.id)
            if not (agent.prompt or "").strip():
                agent.prompt = self._default_prompt(agent.agent_type)
                self._agents[agent.id] = agent

    @staticmethod
    def _default_prompt(agent_type) -> str:
        key = agent_type.value if hasattr(agent_type, "value") else str(agent_type)
        return stored_prompt(key) or DEFAULT_PROMPTS.get(agent_type, "")

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
            model_name=data.model_name or "deepseek-v4",
            temperature=data.temperature if data.temperature is not None else 0.7,
            max_tokens=data.max_tokens or 4096,
            skills=data.skills or [],
            prompt=(data.prompt or "").strip() or self._default_prompt(data.agent_type),
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
        self._agents[agent.id] = agent
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
                model_name="deepseek-v4",
                temperature=0.3,
                max_tokens=8192,
                skills=["task_planning", "coordination", "decision_making"],
                enabled=True
            ),
            AgentConfigCreate(
                name="BugFix Agent",
                agent_type=AgentType.BUG_FIX,
                description="Bug 修复专家，负责分析和修复代码缺陷",
                model_name="deepseek-v4",
                temperature=0.2,
                max_tokens=4096,
                skills=["code_analysis", "debugging", "patch_generation"],
                enabled=True
            ),
            AgentConfigCreate(
                name="Feature Design Agent",
                agent_type=AgentType.FEATURE_DESIGN,
                description="功能设计专家，负责需求分析和方案设计",
                model_name="deepseek-v4",
                temperature=0.5,
                max_tokens=8192,
                skills=["requirement_analysis", "architecture_design", "documentation"],
                enabled=True
            ),
            AgentConfigCreate(
                name="CodeGen Agent",
                agent_type=AgentType.CODE_GENERATION,
                description="代码生成专家，负责编写和优化代码",
                model_name="deepseek-v4",
                temperature=0.2,
                max_tokens=4096,
                skills=["code_generation", "refactoring", "optimization"],
                enabled=True
            ),
            AgentConfigCreate(
                name="Test Agent",
                agent_type=AgentType.TEST_EXECUTION,
                description="测试执行专家，负责测试用例生成和执行",
                model_name="deepseek-v4",
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
