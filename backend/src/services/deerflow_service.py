"""DeerFlow 集成服务

通过 DeerFlowClient 嵌入式调用 DeerFlow Agent 系统。
提供需求分析、方案生成、代码生成、测试执行等完整运维工作流。
"""

import os
import sys
import json
import logging
import re
from typing import Any, Dict, List, Optional, Generator, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from uuid import UUID

logger = logging.getLogger(__name__)

OPSPILOT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = OPSPILOT_ROOT.parent
HARNESS_CANDIDATES = [
    WORKSPACE_ROOT / "deerflow" / "backend" / "packages" / "harness",
    OPSPILOT_ROOT / "deerflow" / "backend" / "packages" / "harness",
    WORKSPACE_ROOT / "deer-flow-study" / "backend" / "packages" / "harness",
]
CONFIG_CANDIDATES = [
    WORKSPACE_ROOT / "config.yaml",
    OPSPILOT_ROOT / "deerflow" / "config.yaml",
    WORKSPACE_ROOT / "deer-flow-study" / "config.yaml",
]

for harness_path in HARNESS_CANDIDATES:
    if harness_path.exists():
        candidate = str(harness_path)
        if candidate not in sys.path:
            sys.path.insert(0, candidate)
        break

resolved_config = next((path for path in CONFIG_CANDIDATES if path.exists()), None)
if resolved_config is not None:
    os.environ.setdefault("DEER_FLOW_CONFIG_PATH", str(resolved_config))

for skills_path in (WORKSPACE_ROOT / "skills", OPSPILOT_ROOT / "skills"):
    if skills_path.exists():
        os.environ.setdefault("DEER_FLOW_SKILLS_PATH", str(skills_path))
        break

os.environ.setdefault("DEER_FLOW_HOME", str(OPSPILOT_ROOT / ".opspilot"))


@dataclass
class AgentResponse:
    """Agent 响应结构"""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[str] = None
    events: List[Dict[str, Any]] = field(default_factory=list)


class DeerFlowService:
    """DeerFlow 集成服务
    
    封装 DeerFlowClient，提供运维场景的 Agent 调用能力。
    """
    
    _instance = None
    _client = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._try_initialize()
            DeerFlowService._initialized = True
    
    def _resolve_config_path(self) -> Optional[Path]:
        """选择一份 DeerFlow 能加载的配置。"""
        for config_path in CONFIG_CANDIDATES:
            if config_path.exists():
                return config_path
        return None

    def _try_initialize(self):
        """尝试初始化 DeerFlow Client"""
        try:
            from deerflow.client import DeerFlowClient

            config_path = self._resolve_config_path()
            if config_path is not None:
                os.environ["DEER_FLOW_CONFIG_PATH"] = str(config_path)
            self._client = DeerFlowClient()
            logger.info("DeerFlow Client 初始化成功，配置: %s", config_path)
        except ImportError as e:
            logger.warning(f"DeerFlow 未安装或导入失败: {e}")
            logger.info("DeerFlow 不可用，对话接口将返回失败")
            self._client = None
        except Exception as e:
            logger.error(f"DeerFlow Client 初始化失败: {e}")
            logger.info("将使用模拟模式运行")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """检查 DeerFlow 是否可用"""
        return self._client is not None
    
    def _retrieve_project_knowledge(
        self,
        message: str,
        project_id: Optional[str],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """按对话所属项目做语义检索，并把结果写进发给模型的问题。"""
        if not project_id:
            return message, []
        try:
            parsed_project_id = UUID(str(project_id))
        except ValueError:
            return message, []

        from .agent_runtime import agent_runtime

        if not agent_runtime.skill_enabled(parsed_project_id, "knowledge-retrieval"):
            return message, []

        from .project_service import project_service

        project_service.record_skill_use(parsed_project_id, "knowledge-retrieval")

        from .knowledge_service import knowledge_service

        hits = knowledge_service.search_knowledge(
            parsed_project_id,
            message,
            top_k=5,
            snippet_chars=1000,
        )
        sources: List[Dict[str, Any]] = []
        sections: List[str] = []
        for index, hit in enumerate(hits, start=1):
            knowledge_base = knowledge_service.get_knowledge_base(hit.knowledge_base_id)
            knowledge_base_name = knowledge_base.name if knowledge_base else ""
            preview = hit.content_snippet if len(hit.content_snippet) <= 200 else hit.content_snippet[:200] + "..."
            sources.append({
                "title": hit.title,
                "snippet": preview,
                "score": hit.score,
                "knowledge_base_name": knowledge_base_name,
                "document_id": str(hit.document_id),
            })
            location = f"（知识库：{knowledge_base_name}）" if knowledge_base_name else ""
            sections.append(f"{index}. 文档《{hit.title}》{location}\n{hit.content_snippet}")

        if not sections:
            return message, []

        grounded = (
            "请作为该项目的运维助手回答。优先使用下面从该项目知识库检索到的内容；"
            "这些内容与问题相关时，回答必须依据它们。"
            "如果检索结果不能回答问题，请明确说明知识库中没有对应资料，不要编造文档中不存在的事实。\n\n"
            "## 项目知识库检索结果\n"
            + "\n\n".join(sections)
            + "\n\n## 用户问题\n"
            + message
        )
        return grounded, sources

    def _with_classification_instruction(self, message: str) -> str:
        """要求模型先按语义判断问题类型，再回答。"""
        return (
            "请先判断用户这句话属于哪一类，并且第一个输出必须是 json 代码块，代码块前不要写任何文字。"
            "格式固定为："
            '{"type":"bug","priority":"medium","title":"一句话标题"}。'
            "type 只能是 bug、feature、question："
            "bug 表示现有功能出错、异常、失败或不可用；"
            "feature 表示希望新增或改进功能；"
            "question 表示咨询用法、原因或已有说明。"
            "priority 只能是 high、medium、low。"
            "即使开头有「我遇到了一个 Bug」或「我有一个新需求」这类前缀，也要以后面的具体描述为准。"
            "输出代码块后，再用 Markdown 回答。\n\n"
            + message
        )

    def _extract_classification(self, text: str) -> Tuple[str, Optional[Dict[str, str]]]:
        """从回复里取出分类，并从展示文本中去掉这段 JSON。"""
        patterns = (
            r"```json\s*(\{.*?\})\s*```",
            r"```\s*(\{.*?\})\s*```",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if not match:
                continue
            parsed = self._parse_classification(match.group(1))
            if not parsed:
                continue
            visible = (text[:match.start()] + text[match.end():]).strip()
            return visible, parsed

        stripped = text.lstrip()
        if stripped.startswith("{"):
            end = stripped.find("}")
            if end != -1:
                parsed = self._parse_classification(stripped[:end + 1])
                if parsed:
                    return stripped[end + 1:].strip(), parsed
        return text, None

    def _parse_classification(self, raw: str) -> Optional[Dict[str, str]]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        kind = str(data.get("type") or "").lower()
        if kind not in {"bug", "feature", "question"}:
            return None
        priority = str(data.get("priority") or "medium").lower()
        if priority == "critical":
            priority = "high"
        if priority not in {"high", "medium", "low"}:
            priority = "medium"
        title = " ".join(str(data.get("title") or "").split())
        return {"type": kind, "priority": priority, "title": title[:80]}

    def _fallback_classification(self, message: str) -> Dict[str, str]:
        from .lead_agent_service import lead_agent_service

        analysis = lead_agent_service.analyze_requirement(message)
        priority = analysis.priority.value
        if priority == "critical":
            priority = "high"
        if priority not in {"high", "medium", "low"}:
            priority = "medium"
        return {
            "type": analysis.type.value,
            "priority": priority,
            "title": "",
        }

    def chat(
        self,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> AgentResponse:
        """发送消息给 Agent
        
        Args:
            message: 用户消息
            thread_id: 会话 ID（可选，用于多轮对话）
            context: 额外上下文
            
        Returns:
            AgentResponse: Agent 响应
        """
        grounded_message, sources = self._retrieve_project_knowledge(message, project_id)
        prepared, model_name, lead_error = self._lead_turn(
            self._with_classification_instruction(grounded_message),
            project_id,
        )
        if lead_error:
            return AgentResponse(
                success=False,
                message=lead_error,
                thread_id=thread_id,
                data={"project_id": project_id, "knowledge_results": sources},
            )
        classification = self._classified(message, None)
        if not self.is_available:
            return AgentResponse(
                success=True,
                message="已完成语义分类。DeerFlow 当前不可用，暂时无法生成进一步说明。",
                thread_id=thread_id,
                data={
                    "project_id": project_id,
                    "knowledge_results": sources,
                    "classification": classification,
                },
            )
        
        try:
            response = self.complete_text(prepared, model_name=model_name)
            if not response.success:
                raise RuntimeError(response.message or "模型没有生成回复")
            visible, parsed = self._extract_classification(response.message)
            classification = self._classified(message, parsed)
            
            return AgentResponse(
                success=True,
                message=visible or response.message,
                thread_id=thread_id,
                data={
                    "raw_response": response.message,
                    "project_id": project_id,
                    "knowledge_results": sources,
                    "classification": classification,
                }
            )
            
        except Exception as e:
            logger.error(f"DeerFlow chat 失败: {e}")
            return AgentResponse(
                success=True,
                message=f"已完成语义分类。生成详细回复失败：{e}",
                thread_id=thread_id,
                data={
                    "project_id": project_id,
                    "knowledge_results": sources,
                    "classification": classification,
                },
            )

    def _classified(self, message: str, parsed: Optional[Dict[str, str]]) -> Dict[str, str]:
        """保证每条对话都有语义分类。模型没给出时使用本地判断。"""
        classification = parsed or self._fallback_classification(message)
        if not classification.get("title"):
            classification["title"] = " ".join(message.split())[:40]
        return classification

    def _lead_turn(self, message: str, project_id: Optional[str]) -> Tuple[str, Optional[str], Optional[str]]:
        """用项目的 Lead Agent 包装任务。返回文本、模型名和禁用原因。"""
        if not project_id:
            return message, None, None
        try:
            parsed_project_id = UUID(str(project_id))
        except ValueError:
            return message, None, None
        from ..models.agent import AgentType
        from .agent_runtime import AgentDisabledError, agent_runtime

        try:
            agent = agent_runtime.require(parsed_project_id, AgentType.LEAD)
        except AgentDisabledError as exc:
            return message, None, str(exc)
        return agent_runtime.render_task(agent, message), agent.model_name, None

    def complete(
        self,
        message: str,
        thread_id: Optional[str] = None,
        *,
        model_name: Optional[str] = None,
        recursion_limit: Optional[int] = None,
    ) -> AgentResponse:
        """直接让模型完成一项任务，不挂载搜索和网页抓取。"""
        if recursion_limit is not None:
            logger.info("忽略 recursion_limit=%s，本次不使用工具循环", recursion_limit)
        if not self.is_available:
            return AgentResponse(
                success=False,
                message="DeerFlow 未安装，当前无法生成代码",
                thread_id=thread_id,
            )
        response = self.complete_text(message, model_name=model_name)
        response.thread_id = thread_id
        return response

    def complete_text(
        self,
        message: str,
        *,
        model_name: Optional[str] = None,
    ) -> AgentResponse:
        """直接调用配置中的模型生成正文，不挂载搜索、抓取或其他工具。"""
        if not self.is_available:
            return AgentResponse(
                success=False,
                message="DeerFlow 未安装，当前无法生成方案",
            )
        try:
            from langchain_core.messages import HumanMessage
            from deerflow.models.factory import create_chat_model

            model = create_chat_model(
                name=model_name,
                thinking_enabled=False,
                attach_tracing=False,
            )
            result = model.invoke([HumanMessage(content=message)])
            text = self._message_text(result)
            if not text:
                return AgentResponse(success=False, message="模型没有返回方案正文")
            return AgentResponse(success=True, message=text)
        except Exception as e:
            logger.error(f"模型直接生成失败: {e}")
            return AgentResponse(
                success=False,
                message=f"Agent 调用失败: {str(e)}",
            )

    @staticmethod
    def _message_text(message: Any) -> str:
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict):
                    parts.append(str(block.get("text") or ""))
            return "\n".join(part.strip() for part in parts if part and part.strip()).strip()
        return str(content or "").strip()
    
    def stream(
        self,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """流式发送消息给 Agent
        
        Args:
            message: 用户消息
            thread_id: 会话 ID
            context: 额外上下文
            
        Yields:
            Dict: 流式事件
        """
        if not self.is_available:
            yield {
                "type": "error",
                "data": {"error": "DeerFlow 未安装，当前无法生成回复"},
            }
            return
        
        try:
            grounded_message, sources = self._retrieve_project_knowledge(message, project_id)
            prepared, model_name, lead_error = self._lead_turn(grounded_message, project_id)
            if lead_error:
                yield {"type": "error", "data": {"error": lead_error}}
                return
            if sources:
                yield {"type": "knowledge", "data": {"results": sources, "project_id": project_id}}
            options = {"model_name": model_name} if model_name else {}
            for event in self._client.stream(prepared, thread_id=thread_id, **options):
                yield {
                    "type": event.type,
                    "data": event.data
                }
                
        except Exception as e:
            logger.error(f"DeerFlow stream 失败: {e}")
            yield {
                "type": "error",
                "data": {"error": str(e)}
            }
    
    def analyze_requirement(
        self,
        title: str,
        description: str,
        source: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """分析运维需求
        
        使用 requirement-analysis skill 分析需求。
        
        Args:
            title: 需求标题
            description: 需求描述
            source: 来源（github_issue, jira, alert 等）
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 分析结果
        """
        prompt = f"""请使用 requirement-analysis 技能分析以下运维需求：

## 需求标题
{title}

## 需求描述
{description}

## 来源
{source or '用户提交'}

请输出结构化的分析结果，包括：
1. 需求类型（bug/feature/enhancement/maintenance/security）
2. 优先级（P0-P3）
3. 影响评估
4. 复杂度评估
5. 相关知识库检索结果
6. 建议的下一步行动
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "requirement-analysis",
                "agent_name": "requirement_analyzer"
            }
        )
    
    def generate_bugfix_solution(
        self,
        requirement_id: str,
        analysis: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """生成 Bug 修复方案
        
        使用 bugfix-solution skill 生成修复方案。
        
        Args:
            requirement_id: 需求 ID
            analysis: 需求分析结果
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 修复方案
        """
        prompt = f"""请使用 bugfix-solution 技能为以下 Bug 生成修复方案：

## 需求 ID
{requirement_id}

## 需求分析
{json.dumps(analysis, ensure_ascii=False, indent=2)}

请输出完整的修复方案，包括：
1. 根因分析
2. 修复策略
3. 代码变更建议
4. 测试计划
5. 回滚方案
6. 风险评估
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "bugfix-solution",
                "agent_name": "bugfix_agent"
            }
        )
    
    def generate_feature_design(
        self,
        requirement_id: str,
        analysis: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """生成功能设计方案
        
        使用 feature-design skill 生成设计方案。
        
        Args:
            requirement_id: 需求 ID
            analysis: 需求分析结果
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 设计方案
        """
        prompt = f"""请使用 feature-design 技能为以下功能需求生成设计方案：

## 需求 ID
{requirement_id}

## 需求分析
{json.dumps(analysis, ensure_ascii=False, indent=2)}

请输出完整的设计方案，包括：
1. 功能概述和用户故事
2. 功能范围（in_scope / out_of_scope）
3. 技术架构设计
4. API 接口设计
5. 数据模型设计
6. 实施计划和里程碑
7. 测试策略
8. 风险评估
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "feature-design",
                "agent_name": "feature_agent"
            }
        )
    
    def generate_code(
        self,
        solution_id: str,
        solution: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """生成代码
        
        使用 code-generation skill 生成代码。
        
        Args:
            solution_id: 方案 ID
            solution: 解决方案
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 生成的代码
        """
        prompt = f"""请使用 code-generation 技能根据以下方案生成代码：

## 方案 ID
{solution_id}

## 解决方案
{json.dumps(solution, ensure_ascii=False, indent=2)}

请输出：
1. 代码文件列表和内容
2. 单元测试代码
3. API 文档
4. 变更说明
5. 代码质量检查结果
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "code-generation",
                "agent_name": "codegen_agent"
            }
        )
    
    def execute_tests(
        self,
        code_changes: List[Dict[str, Any]],
        test_type: str = "all",
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """执行测试
        
        使用 test-execution skill 执行测试。
        
        Args:
            code_changes: 代码变更列表
            test_type: 测试类型（unit/integration/all）
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 测试结果
        """
        prompt = f"""请使用 test-execution 技能执行以下测试：

## 测试类型
{test_type}

## 代码变更
{json.dumps(code_changes, ensure_ascii=False, indent=2)}

请执行测试并输出：
1. 测试结果汇总
2. 各测试套件详情
3. 失败用例分析
4. 覆盖率报告
5. 质量门禁检查结果
6. 建议的下一步行动
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "test-execution",
                "agent_name": "test_agent"
            }
        )
    
    def search_knowledge(
        self,
        query: str,
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """搜索知识库
        
        使用 knowledge-retrieval skill 搜索知识库。
        
        Args:
            query: 搜索查询
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 搜索结果
        """
        prompt = f"""请使用 knowledge-retrieval 技能搜索以下内容：

## 搜索查询
{query}

请返回：
1. 相关文档列表
2. 历史 Issue 案例
3. 最佳实践参考
4. 相关代码示例
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "knowledge-retrieval"
            }
        )


# 单例实例
deerflow_service = DeerFlowService()
