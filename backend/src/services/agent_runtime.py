"""按项目里的 Agent 配置执行任务。"""

import json
import re
from typing import Optional
from uuid import UUID

from ..models.agent import AgentConfig, AgentType
from ..models.requirement import RequirementAnalysis, RequirementPriority, RequirementType


class AgentDisabledError(RuntimeError):
    """项目里对应的 Agent 不存在或未启用。"""


PRIMARY_SKILL = {
    AgentType.LEAD: "requirement-analysis",
    AgentType.BUG_FIX: "bugfix-solution",
    AgentType.FEATURE_DESIGN: "feature-design",
    AgentType.CODE_GENERATION: "code-generation",
    AgentType.TEST_EXECUTION: "test-execution",
}


class AgentRuntime:
    """读取项目 Agent 配置，并把提示词、模型和技能带进实际任务。"""

    def get(self, project_id: UUID, agent_type: AgentType) -> Optional[AgentConfig]:
        from .agent_service import agent_service

        for agent in agent_service.get_agents_by_project(project_id):
            if agent.agent_type == agent_type:
                return agent
        return None

    def require(self, project_id: UUID, agent_type: AgentType) -> AgentConfig:
        agent = self.get(project_id, agent_type)
        name = agent.name if agent else agent_type.value
        if agent is None or not agent.enabled:
            raise AgentDisabledError(f"{name} 未启用，这一阶段不会执行")
        self._require_skill(project_id, agent_type, name)
        return agent

    def _require_skill(self, project_id: UUID, agent_type: AgentType, agent_name: str) -> None:
        from .project_service import project_service

        project = project_service.get(project_id)
        key = PRIMARY_SKILL.get(agent_type)
        if project is None or not key:
            return
        skill = next((item for item in project.skills if item.key == key), None)
        if skill is not None and not skill.enabled:
            raise AgentDisabledError(f"{skill.name} 未启用，{agent_name} 不会执行")

    def skill_enabled(self, project_id: UUID, key: str) -> bool:
        from .project_service import project_service

        project = project_service.get(project_id)
        if project is None:
            return True
        skill = next((item for item in project.skills if item.key == key), None)
        return True if skill is None else skill.enabled

    def render_task(self, agent: AgentConfig, task: str) -> str:
        from .project_service import project_service

        skills = "、".join(agent.skills) if agent.skills else "无"
        prompt = (agent.prompt or "").strip() or "按你的职责完成任务。"
        project = project_service.get(agent.project_id)
        project_prompt = (getattr(project, "prompt_template", "") or "").strip() if project else ""
        toolchain = (getattr(project, "toolchain", "") or "").strip() if project else ""
        sections = [prompt]
        if project_prompt:
            sections.append(f"项目级 Prompt：\n{project_prompt}")
        if toolchain:
            sections.append(f"项目工具链：\n{toolchain}")
        if project is not None:
            enabled = [item.name for item in project.skills if item.enabled]
            if enabled:
                sections.append("已启用的项目技能：" + "、".join(enabled))
        sections.append(
            "执行约束：\n"
            f"- 模型：{agent.model_name}\n"
            f"- temperature：{agent.temperature}\n"
            f"- 输出长度不超过 {agent.max_tokens} tokens\n"
            f"- 可使用的技能：{skills}"
        )
        sections.append(f"任务：\n{task}")
        self._record_primary_skill(agent)
        return "\n\n".join(sections)

    def _record_primary_skill(self, agent: AgentConfig) -> None:
        from .project_service import project_service

        kind = agent.agent_type
        if not isinstance(kind, AgentType):
            try:
                kind = AgentType(str(kind))
            except ValueError:
                return
        key = PRIMARY_SKILL.get(kind)
        if key:
            project_service.record_skill_use(agent.project_id, key)

    def complete(
        self,
        agent: AgentConfig,
        task: str,
        thread_id: Optional[str] = None,
        recursion_limit: Optional[int] = None,
    ):
        from .deerflow_service import deerflow_service

        return deerflow_service.complete(
            self.render_task(agent, task),
            thread_id=thread_id,
            model_name=agent.model_name,
            recursion_limit=recursion_limit,
        )

    def advise(self, agent: AgentConfig, task: str) -> str:
        from .deerflow_service import deerflow_service

        if not deerflow_service.is_available:
            return ""
        response = deerflow_service.complete_text(
            self.render_task(agent, task),
            model_name=agent.model_name,
        )
        if not response.success:
            raise RuntimeError(response.message or "模型没有生成方案")
        return (response.message or "").strip()

    def analyze_requirement(self, agent: AgentConfig, text: str) -> RequirementAnalysis:
        from .deerflow_service import deerflow_service
        from .lead_agent_service import lead_agent_service

        if deerflow_service.is_available:
            task = (
                "分析下面的运维需求，只输出一个 json 对象，不要写其他文字。"
                "字段：type（bug、feature、question）、priority（critical、high、medium、low）、"
                "keywords（字符串数组）、confidence（0 到 1 的小数）。\n\n"
                + text
            )
            response = self.complete(agent, task)
            parsed = self._parse_analysis(response.message if response.success else "")
            if parsed is not None:
                return parsed
        return lead_agent_service.analyze_requirement(text)

    def _parse_analysis(self, text: str) -> Optional[RequirementAnalysis]:
        match = re.search(r"\{.*\}", text or "", re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        kind = str(data.get("type") or "").lower()
        if kind not in {item.value for item in RequirementType}:
            return None
        priority = str(data.get("priority") or "medium").lower()
        if priority not in {item.value for item in RequirementPriority}:
            priority = "medium"
        keywords = data.get("keywords") or []
        if not isinstance(keywords, list):
            keywords = []
        try:
            confidence = float(data.get("confidence") or 0.6)
        except (TypeError, ValueError):
            confidence = 0.6
        confidence = min(max(confidence, 0.0), 1.0)
        return RequirementAnalysis(
            type=RequirementType(kind),
            priority=RequirementPriority(priority),
            keywords=[str(item) for item in keywords if str(item).strip()][:12],
            confidence=confidence,
        )


agent_runtime = AgentRuntime()
