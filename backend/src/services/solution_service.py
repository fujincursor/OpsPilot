"""方案管理服务"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Union, TYPE_CHECKING
from uuid import UUID

from ..models.requirement import Requirement, RequirementType, RequirementStatus
from ..models.solution import (
    Solution,
    BugFixSolution,
    FeatureDesignSolution,
    SolutionType,
    SolutionStatus,
    SolutionUpdate,
    SolutionFilters,
    ImpactAnalysis,
    ImpactLevel,
)
from ..db import DocumentDict
from .agents.bugfix_agent import bugfix_agent_service
from .agents.feature_agent import feature_agent_service

if TYPE_CHECKING:
    from .requirement_service import RequirementService
    from .knowledge_service import KnowledgeService


_SECTION_HEADING = re.compile(r"^(#{2,4})\s+(.+?)\s*$", re.MULTILINE)
_STEP_LINE = re.compile(r"^(?:[-*]|\d+[.)、])\s+(.+?)\s*$", re.MULTILINE)
_FILE_EXTENSIONS = r"py|tsx|ts|jsx|js|vue|go|java|kt|sql|json|css|scss|html|md|yml|yaml|xml"
_FILE_IN_TICKS = re.compile(rf"`([^`\n]*?\.(?:{_FILE_EXTENSIONS}))`")
_FILE_BARE = re.compile(
    rf"(?<![\w./-])((?:[\w.-]+/)+[\w.-]+\.(?:{_FILE_EXTENSIONS}))"
)


def _section_body(text: str, keywords: tuple[str, ...]) -> str:
    """取出标题里包含指定词的那一节，并保留它下面的子标题。"""
    matches = list(_SECTION_HEADING.finditer(text or ""))
    for index, match in enumerate(matches):
        title = re.sub(r"^\d+(?:\.\d+)*[.、]?\s*", "", match.group(2)).strip()
        if not any(word in title for word in keywords):
            continue
        level = len(match.group(1))
        end = len(text)
        for later in matches[index + 1:]:
            if len(later.group(1)) <= level:
                end = later.start()
                break
        return text[match.end():end].strip()
    return ""


def _step_lines(section: str) -> List[str]:
    steps: List[str] = []
    for match in _STEP_LINE.finditer(section or ""):
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", match.group(1)).strip()
        if line and line not in steps:
            steps.append(line)
    return steps


def affected_files_from_content(content: str) -> List[str]:
    """从方案正文里取出这条需求自己的文件路径。"""
    found: List[str] = []
    for pattern in (_FILE_IN_TICKS, _FILE_BARE):
        for match in pattern.finditer(content or ""):
            path = match.group(1).strip().strip("`").replace("\\", "/")
            while path.startswith("./"):
                path = path[2:]
            if not path or path.startswith("http") or " " in path:
                continue
            if path not in found:
                found.append(path)
    covered = {
        path.rsplit("/", 1)[-1]
        for path in found
        if "/" in path
    }
    return [
        path for path in found
        if "/" in path or path not in covered
    ]


def _strip_fences(text: str) -> str:
    return re.sub(r"```[^\n]*\n.*?```", "", text or "", flags=re.S)


def _generic_steps() -> set[str]:
    canned = {
        "收集完整的错误日志和上下文信息",
        "分析错误发生的条件和频率",
        "定位问题代码位置",
        "制定修复方案并评审",
        "实施修复并进行充分测试",
    }
    for items in bugfix_agent_service.FIX_TEMPLATES.values():
        canned.update(items)
    return canned


def _is_generic_step(line: str) -> bool:
    text = re.sub(r"^\d+[.、)\]]\s*", "", line or "").strip()
    return text in _generic_steps() or any(text.endswith(item) for item in _generic_steps())


def _child_sections(section: str) -> List[tuple[str, str]]:
    matches = list(_SECTION_HEADING.finditer(section or ""))
    if not matches:
        return []
    top = min(len(match.group(1)) for match in matches)
    children: List[tuple[str, str]] = []
    for index, match in enumerate(matches):
        if len(match.group(1)) != top:
            continue
        end = len(section)
        for later in matches[index + 1:]:
            if len(later.group(1)) <= top:
                end = later.start()
                break
        title = re.sub(r"^\d+(?:\.\d+)*[.、]?\s*", "", match.group(2)).strip()
        children.append((title, section[match.end():end].strip()))
    return children


def _steps_in_section(section: str) -> List[str]:
    body = _strip_fences(section)
    children = _child_sections(body)
    steps: List[str] = []
    if children:
        for title, child in children:
            bullets = [line for line in _step_lines(child) if not _is_generic_step(line)]
            file_line = re.search(r"\*\*文件\*\*[^\n]*", child)
            files = re.findall(r"`([^`]+)`", file_line.group(0)) if file_line else []
            label = title
            if files:
                label = f"{title}（{'、'.join(item.strip() for item in files)}）"
            detail = "；".join(bullets)
            text = f"{label}：{detail}" if detail else label
            if text and not _is_generic_step(text):
                steps.append(text)
        return steps
    return [line for line in _step_lines(body) if not _is_generic_step(line)]


def fix_steps_from_content(content: str) -> List[str]:
    """优先使用正文里针对这条需求写出的修改步骤。"""
    candidates: List[List[str]] = []
    for keywords in (("修复步骤",), ("修改建议", "修改点")):
        section = _section_body(content, keywords)
        steps = _steps_in_section(section) if section else []
        if steps:
            candidates.append(steps)
    return candidates[0] if candidates else []


def bugfix_details_from_content(content: str) -> tuple[str, List[str]]:
    """从方案正文中取出这条需求自己的根因和修复步骤。"""
    root = _section_body(content, ("根因",))
    return root, fix_steps_from_content(content)


def _plain(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text or "").strip()


def _after_colon(line: str) -> str:
    parts = re.split(r"[：:]", line, maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else line.strip()


def _impact_level(text: str) -> ImpactLevel:
    if any(word in text for word in ("高风险", "严重", "核心逻辑")):
        return ImpactLevel.HIGH
    if any(word in text for word in ("中风险", "可能影响", "稳定性")):
        return ImpactLevel.MEDIUM
    return ImpactLevel.LOW


_GENERIC_REGRESSION = (
    "修改范围有限，建议进行基本功能验证",
    "修改可能影响系统稳定性，建议进行针对性回归测试",
    "修改涉及核心逻辑，建议进行完整回归测试，包括压力测试和边界条件测试",
)


def _labeled_block(text: str, label: str) -> str:
    match = re.search(
        rf"(?:^|\n)\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*[：:]\s*(.*?)(?=\n\s*(?:#{{2,4}}\s|\*\*[^*\n]+\*\*\s*[：:])|\Z)",
        text or "",
        re.S,
    )
    return match.group(1).strip() if match else ""


def _table_risk_lines(section: str) -> tuple[List[str], str]:
    """从影响范围表里取出中、高风险行，以及其中最高的风险等级。"""
    lines: List[str] = []
    rank = "low"
    for raw in (section or "").splitlines():
        if not raw.strip().startswith("|"):
            continue
        cells = [_plain(cell).strip() for cell in raw.strip().strip("|").split("|")]
        if len(cells) < 3 or all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            continue
        if cells[0] in {"影响面", "模块", "范围"} or "风险" in cells[-1] and "影响" in cells[0]:
            continue
        risk_cell = cells[-1]
        if risk_cell.startswith("高"):
            rank = "high"
        elif risk_cell.startswith("中") and rank != "high":
            rank = "medium"
        else:
            continue
        lines.append(f"{cells[0]}：{cells[1]}（{risk_cell}）")
    return lines, rank


def _regression_from_content(content: str) -> str:
    """从方案正文中取出这条需求自己的回归风险，跳过固定套话。"""
    parts: List[str] = []
    rank = ""
    direct = _section_body(content, ("回归风险", "回归评估"))
    direct_plain = _plain(_strip_fences(direct))
    if direct_plain and not any(marker in direct_plain for marker in _GENERIC_REGRESSION):
        bullets = _step_lines(_strip_fences(direct))
        parts.extend(bullets or [direct_plain[:800]])
    else:
        block = _labeled_block(content, "回归")
        if block and not any(marker in block for marker in _GENERIC_REGRESSION):
            parts.extend(_step_lines(block) or [_plain(block)])
        table_lines, table_rank = _table_risk_lines(_section_body(content, ("影响范围", "影响分析")))
        if table_rank == "high":
            rank = "高风险"
        elif table_rank == "medium":
            rank = "中风险"
        parts.extend(table_lines)
    cleaned: List[str] = []
    for part in parts:
        text = _plain(part)
        if not text or any(marker in text for marker in _GENERIC_REGRESSION):
            continue
        if text not in cleaned:
            cleaned.append(text)
    if not cleaned:
        return ""
    if not rank:
        blob = " ".join(cleaned)
        if "高风险" in blob or "高；" in blob:
            rank = "高风险"
        elif "中风险" in blob or "中；" in blob or "可能影响" in blob:
            rank = "中风险"
        else:
            rank = "低风险"
    areas: List[str] = []
    for match in re.finditer(r"`([^`]+)`|([\w./-]+\.(?:py|tsx|ts|jsx|js))", "\n".join(cleaned)):
        name = (match.group(1) or match.group(2) or "").strip()
        short = name.rsplit("/", 1)[-1]
        if short and re.search(r"\.(?:py|tsx|ts|jsx|js)$", short) and short not in areas:
            areas.append(short)
    body = "\n".join(f"- {item}" for item in cleaned)
    area_line = f"\n\n可能影响{'、'.join(areas)}。" if areas else ""
    return f"{rank}: \n{body}{area_line}"


def bugfix_assessment_from_content(content: str) -> tuple[Optional[ImpactAnalysis], str]:
    """从方案正文中取出这条需求自己的影响分析和回归风险。"""
    section = _section_body(content, ("影响范围", "影响分析"))
    bullets = _step_lines(section)
    if not section and not bullets:
        regression = _regression_from_content(content)
        return None, regression

    scope_parts: List[str] = []
    risk_points: List[str] = []
    modules: List[str] = []
    regression = ""
    for line in bullets or [_plain(section)]:
        body = _after_colon(line)
        if "回归风险" in line[:8] or line.startswith("回归"):
            regression = body
            continue
        if "功能影响" in line[:8] or line.startswith("功能"):
            scope_parts.append(body)
        else:
            risk_points.append(body)
        for match in re.finditer(r"(?<!不)影响\s*([^，。；的]+)", body):
            name = match.group(1).strip()
            if name and name not in modules and "不" not in name:
                modules.append(name)

    plain_scope = "；".join(scope_parts) if scope_parts else _plain(section)
    level = _impact_level(plain_scope)
    _, table_rank = _table_risk_lines(section)
    if table_rank == "high":
        level = ImpactLevel.HIGH
    elif table_rank == "medium" and level not in {ImpactLevel.HIGH, ImpactLevel.CRITICAL}:
        level = ImpactLevel.MEDIUM
    scope = section.strip() or plain_scope
    impact = ImpactAnalysis(
        level=level,
        scope=scope,
        affected_modules=modules,
        risk_points=risk_points,
    )
    regression = _regression_from_content(content) or regression
    if not regression or any(marker in regression for marker in _GENERIC_REGRESSION):
        return impact, ""
    if regression.startswith(("高风险", "中风险", "低风险")):
        return impact, regression
    risk_level = _impact_level(regression)
    prefix = {ImpactLevel.HIGH: "高风险", ImpactLevel.MEDIUM: "中风险"}.get(risk_level, "低风险")
    return impact, f"{prefix}: {regression}"


def _model_failure_text(exc: BaseException) -> str:
    text = str(exc)
    if "Recursion limit" in text or "GRAPH_RECURSION_LIMIT" in text:
        return "模型反复调用网页抓取，Jina 连接超时后达到递归上限。已保留本地草稿，页面可以继续刷新。"
    if "ConnectTimeout" in text or "Jina" in text:
        return "Jina 页面抓取连接超时。已保留本地草稿，页面可以继续刷新。"
    return (text.strip() or "模型没有生成方案")[:1000]


def _assigned_skill(project_id: UUID, agent_type) -> tuple[str, str]:
    from .agent_runtime import PRIMARY_SKILL
    from .project_service import project_service

    key = PRIMARY_SKILL.get(agent_type, "")
    project = project_service.get(project_id)
    skill = next((item for item in project.skills if item.key == key), None) if project else None
    return key, (skill.name if skill and skill.name else key)


class SolutionService:
    """方案管理服务

    负责方案的 CRUD 操作，以及调用对应的 Agent 生成方案。
    方案数据保存在数据库中。
    """

    def __init__(self):
        self._solutions: Dict[UUID, Union[Solution, BugFixSolution, FeatureDesignSolution]] = DocumentDict(
            "solutions",
            model=Solution,
            loader=self._load_solution,
        )
        self._requirement_to_solutions: Dict[UUID, List[UUID]] = {}
        for solution in self._solutions.values():
            self._requirement_to_solutions.setdefault(solution.requirement_id, []).append(solution.id)

    @staticmethod
    def _load_solution(payload: dict) -> Union[Solution, BugFixSolution, FeatureDesignSolution]:
        kind = payload.get("type")
        if kind == SolutionType.BUGFIX.value:
            return BugFixSolution.model_validate(payload)
        if kind == SolutionType.FEATURE_DESIGN.value:
            return FeatureDesignSolution.model_validate(payload)
        return Solution.model_validate(payload)
        self._requirement_service: Optional["RequirementService"] = None
        self._knowledge_service: Optional["KnowledgeService"] = None

    def set_requirement_service(self, requirement_service: "RequirementService"):
        """设置需求服务引用"""
        self._requirement_service = requirement_service

    def set_knowledge_service(self, knowledge_service: "KnowledgeService"):
        """设置知识库服务引用"""
        self._knowledge_service = knowledge_service

    def generate_solution(
        self,
        requirement_id: UUID,
        force_regenerate: bool = False,
        additional_context: Optional[str] = None,
    ) -> Optional[Union[BugFixSolution, FeatureDesignSolution]]:
        """根据需求类型调用对应 Agent 生成方案

        Args:
            requirement_id: 需求 ID
            force_regenerate: 是否强制重新生成
            additional_context: 额外上下文信息

        Returns:
            生成的方案，需求不存在返回 None
        """
        if not self._requirement_service:
            raise RuntimeError("RequirementService not set")

        requirement = self._requirement_service.get(requirement_id)
        if not requirement:
            return None
        if requirement.type == RequirementType.QUESTION:
            return None

        existing_solutions = self._solutions_for(requirement_id)
        if not force_regenerate:
            pending_solutions = [
                item for item in existing_solutions
                if item.status == SolutionStatus.PENDING_REVIEW
            ]
            if pending_solutions:
                return pending_solutions[0]
            draft_solutions = [
                item for item in existing_solutions
                if item.status == SolutionStatus.DRAFT
            ]
            if draft_solutions:
                return draft_solutions[0]

        from ..models.agent import AgentType
        from .agent_runtime import agent_runtime

        agent_type = AgentType.BUG_FIX if requirement.type == RequirementType.BUG else AgentType.FEATURE_DESIGN
        agent = agent_runtime.require(requirement.project_id, agent_type)
        if requirement.type == RequirementType.BUG:
            solution = self._generate_bugfix_solution(requirement, additional_context)
        else:
            solution = self._generate_feature_solution(requirement, additional_context)
        model_error = ""
        knowledge_text = self._knowledge_for_prompt(requirement, additional_context)
        from .workspace_service import workspace_service

        source_text, source_paths = workspace_service.context_for_prompt(
            requirement.project_id,
            requirement.title,
            requirement.description or "",
            additional_context or "",
        )
        draft_text = (
            "已导入本地源代码。草稿里的文件路径和通用步骤都不要采用。"
            if source_paths
            else solution.content
        )
        try:
            rewritten = agent_runtime.advise(
                agent,
                "请按你的提示词，只针对下面这一条需求写出完整方案。"
                "修改哪个文件、改哪一个函数，只能依据「本地源代码」里摘出的内容。"
                "这些代码是已经上传到服务器的项目源代码。代码调整只针对这份代码，不要修改运行服务的工作目录。"
                "必须使用二级标题「修复步骤」，每一步写本地源码中的文件、函数和具体改法，"
                "不要写「收集完整的错误日志和上下文信息」这类通用步骤。"
                "必须使用二级标题「回归风险」，写出这次修改可能破坏的现有行为，"
                "不要写「修改范围有限，建议进行基本功能验证」这类套话。"
                "方案里还要写出这条需求自己的原因、影响范围和验证方法。"
                "知识库文档只用来理解背景，不能据此补充本地源代码里没有的文件。"
                "如果本地源代码写明还没有导入，不要编造文件路径，修复步骤只说明需要先导入代码。\n\n"
                f"需求标题：{requirement.title}\n需求描述：{requirement.description}\n\n"
                f"本地源代码：\n{source_text}\n\n"
                f"知识库背景：\n{knowledge_text or '无'}\n\n草稿：\n{draft_text}",
            )
        except RuntimeError as exc:
            model_error = _model_failure_text(exc)
            rewritten = ""
        if rewritten:
            solution.content = rewritten
            self._sync_bugfix_sections(solution)
        workspace_service.align_solution(requirement.project_id, solution, source_paths)
        solution.created_by_agent = agent.name
        solution.skill_key, solution.skill_name = _assigned_skill(requirement.project_id, agent_type)

        self._solutions[solution.id] = solution

        if requirement_id not in self._requirement_to_solutions:
            self._requirement_to_solutions[requirement_id] = []
        self._requirement_to_solutions[requirement_id].append(solution.id)

        self._update_requirement_status(requirement, RequirementStatus.DESIGNING)
        if self._requirement_service:
            self._requirement_service.set_failure_reason(requirement.id, model_error or None)

        return solution

    def _knowledge_for_prompt(
        self,
        requirement: Requirement,
        additional_context: Optional[str] = None,
    ) -> str:
        """取出和这条需求最接近的代码说明，交给模型写修改点。"""
        if not self._knowledge_service:
            return ""
        query = f"{requirement.title} {requirement.description or ''}"
        if additional_context:
            query += f" {additional_context}"
        from .agent_runtime import agent_runtime
        from .project_service import project_service

        if agent_runtime.skill_enabled(requirement.project_id, "knowledge-retrieval"):
            project_service.record_skill_use(requirement.project_id, "knowledge-retrieval")
        try:
            hits = self._knowledge_service.search_knowledge(
                project_id=requirement.project_id,
                query=query,
                top_k=5,
                snippet_chars=800,
            )
        except Exception:
            return ""
        parts = []
        for hit in hits:
            parts.append(f"- {hit.title}\n{hit.content_snippet}")
        return "\n\n".join(parts)

    def _generate_bugfix_solution(
        self,
        requirement: Requirement,
        additional_context: Optional[str] = None,
    ) -> BugFixSolution:
        """生成 Bug 修复方案"""
        knowledge_results = None
        if self._knowledge_service:
            query = f"{requirement.title} {requirement.description}"
            if additional_context:
                query += f" {additional_context}"

            try:
                knowledge_results = self._knowledge_service.search_knowledge(
                    project_id=requirement.project_id,
                    query=query,
                    top_k=5,
                )
            except Exception:
                pass

        solution = bugfix_agent_service.generate_fix_solution(requirement)

        if knowledge_results:
            root_cause_with_knowledge = bugfix_agent_service.find_root_cause(
                requirement, knowledge_results
            )
            solution.root_cause = root_cause_with_knowledge

        return solution

    def _generate_feature_solution(
        self,
        requirement: Requirement,
        additional_context: Optional[str] = None,
    ) -> FeatureDesignSolution:
        """生成功能设计方案"""
        solution = feature_agent_service.generate_design_doc(requirement)
        return solution

    def _update_requirement_status(
        self, requirement: Requirement, status: RequirementStatus
    ):
        """更新需求状态"""
        if self._requirement_service:
            self._requirement_service.update_status(requirement.id, status)

    def get_solutions_by_requirement(
        self,
        requirement_id: UUID,
        filters: Optional[SolutionFilters] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """获取需求的方案列表

        Args:
            requirement_id: 需求 ID
            filters: 过滤条件
            page: 页码
            page_size: 每页数量

        Returns:
            方案列表
        """
        self.collapse_pending_solutions()
        self.align_with_requirement(requirement_id)
        solution_ids = self._requirement_to_solutions.get(requirement_id, [])
        solutions = [
            self._solutions[sid] for sid in solution_ids
            if sid in self._solutions
        ]

        if filters:
            if filters.type:
                solutions = [s for s in solutions if s.type == filters.type]
            if filters.status:
                solutions = [s for s in solutions if s.status == filters.status]
            if filters.created_by_agent:
                solutions = [
                    s for s in solutions
                    if s.created_by_agent == filters.created_by_agent
                ]

        solutions.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return solutions[start:end]

    def count_solutions_by_requirement(
        self,
        requirement_id: UUID,
        filters: Optional[SolutionFilters] = None,
    ) -> int:
        """统计需求的方案数量"""
        solution_ids = self._requirement_to_solutions.get(requirement_id, [])
        solutions = [
            self._solutions[sid] for sid in solution_ids
            if sid in self._solutions
        ]

        if filters:
            if filters.type:
                solutions = [s for s in solutions if s.type == filters.type]
            if filters.status:
                solutions = [s for s in solutions if s.status == filters.status]
            if filters.created_by_agent:
                solutions = [
                    s for s in solutions
                    if s.created_by_agent == filters.created_by_agent
                ]

        return len(solutions)

    def get_solution(
        self, solution_id: UUID
    ) -> Optional[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """获取单个方案

        Args:
            solution_id: 方案 ID

        Returns:
            方案对象，不存在返回 None
        """
        solution = self._solutions.get(solution_id)
        if solution is None:
            return None
        return self._sync_bugfix_sections(solution)

    def _sync_bugfix_sections(self, solution):
        """用正文里的根因、修改点和文件替换通用模板。"""
        content = solution.content or ""
        files = affected_files_from_content(content)
        changed = False
        if files and files != list(getattr(solution, "affected_files", None) or []):
            solution.affected_files = files
            changed = True
        if getattr(solution, "type", None) != SolutionType.BUGFIX:
            if changed:
                solution.updated_at = datetime.utcnow()
                self._solutions[solution.id] = solution
            return solution
        root, steps = bugfix_details_from_content(content)
        impact, regression = bugfix_assessment_from_content(content)
        if root and root != (solution.root_cause or "").strip():
            solution.root_cause = root
            changed = True
        if steps and steps != list(solution.fix_steps or []):
            solution.fix_steps = steps
            changed = True
        if impact is not None and impact.model_dump() != solution.impact_analysis.model_dump():
            solution.impact_analysis = impact
            changed = True
        if regression and regression != (solution.regression_risk or "").strip():
            solution.regression_risk = regression
            changed = True
        if changed:
            solution.updated_at = datetime.utcnow()
            self._solutions[solution.id] = solution
        return solution

    def update_solution(
        self,
        solution_id: UUID,
        data: SolutionUpdate,
    ) -> Optional[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """更新方案

        Args:
            solution_id: 方案 ID
            data: 更新数据

        Returns:
            更新后的方案，不存在返回 None
        """
        solution = self._solutions.get(solution_id)
        if not solution:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(solution, field):
                setattr(solution, field, value)

        solution.updated_at = datetime.utcnow()
        return solution

    def update_solution_status(
        self,
        solution_id: UUID,
        status: SolutionStatus,
        reviewed_by: Optional[str] = None,
        review_comment: Optional[str] = None,
    ) -> Optional[Union[Solution, BugFixSolution, FeatureDesignSolution]]:
        """更新方案状态

        Args:
            solution_id: 方案 ID
            status: 新状态
            reviewed_by: 审核人
            review_comment: 审核意见

        Returns:
            更新后的方案，不存在返回 None
        """
        solution = self._solutions.get(solution_id)
        if not solution:
            return None

        previous = solution.status
        solution.status = status
        solution.updated_at = datetime.utcnow()

        if reviewed_by:
            solution.reviewed_by = reviewed_by

        if review_comment:
            solution.review_comment = review_comment

        self._solutions[solution.id] = solution
        if status == SolutionStatus.DRAFT and previous == SolutionStatus.PENDING_REVIEW:
            self._supersede_open_review(solution, "方案已撤回待审核")
            self._release_requirement_if_idle(solution)

        if status == SolutionStatus.APPROVED:
            requirement = self._requirement_service.get(solution.requirement_id)
            if requirement:
                self._update_requirement_status(requirement, RequirementStatus.CODING)
        elif status == SolutionStatus.IMPLEMENTED:
            requirement = self._requirement_service.get(solution.requirement_id)
            if requirement:
                self._update_requirement_status(requirement, RequirementStatus.TESTING)

        return solution

    def has_pending_solution(self, requirement_id: UUID) -> bool:
        return any(
            item.status == SolutionStatus.PENDING_REVIEW
            for item in self._solutions_for(requirement_id)
        )

    def collapse_pending_solutions(self) -> None:
        """同一条需求只保留最新一份待审核方案，其余作废。"""
        grouped: Dict[UUID, List[Union[Solution, BugFixSolution, FeatureDesignSolution]]] = {}
        for solution in self._solutions.values():
            if solution.status != SolutionStatus.PENDING_REVIEW:
                continue
            grouped.setdefault(solution.requirement_id, []).append(solution)
        for items in grouped.values():
            items.sort(key=lambda item: item.created_at)
            for stale in items[:-1]:
                self._void_solution(stale, "同一需求只保留最新的待审核方案，此方案作废")

    def _solutions_for(self, requirement_id: UUID):
        return [
            self._solutions[solution_id]
            for solution_id in self._requirement_to_solutions.get(requirement_id, [])
            if solution_id in self._solutions
        ]

    def _void_solution(self, solution, reason: str) -> None:
        from ..models.review import ReviewItemType, ReviewStatus
        from .hitl_service import hitl_service

        solution.status = SolutionStatus.REJECTED
        solution.review_comment = reason
        solution.updated_at = datetime.utcnow()
        self._solutions[solution.id] = solution
        review = hitl_service.find_by_item(ReviewItemType.SOLUTION, solution.id)
        if review is not None and review.status in {ReviewStatus.PENDING, ReviewStatus.IN_REVIEW}:
            hitl_service.supersede(review.id, reason)

    def align_with_requirement(self, requirement_id: UUID) -> None:
        """需求还在设计阶段时，待审核方案退回草稿，审核项一并撤回。"""
        if not self._requirement_service:
            return
        requirement = self._requirement_service.get(requirement_id)
        if requirement is None or requirement.status not in {
            RequirementStatus.PENDING,
            RequirementStatus.ANALYZING,
            RequirementStatus.DESIGNING,
        }:
            return
        for solution in self._solutions_for(requirement_id):
            if solution.status == SolutionStatus.PENDING_REVIEW:
                self._withdraw_solution(solution, "需求已退回设计中，方案撤回待审核")

    def _withdraw_solution(self, solution, reason: str) -> None:
        solution.status = SolutionStatus.DRAFT
        solution.review_comment = reason
        solution.updated_at = datetime.utcnow()
        self._solutions[solution.id] = solution
        self._supersede_open_review(solution, reason)

    def _supersede_open_review(self, solution, reason: str) -> None:
        from ..models.review import ReviewItemType, ReviewStatus
        from .hitl_service import hitl_service

        review = hitl_service.find_by_item(ReviewItemType.SOLUTION, solution.id)
        if review is not None and review.status in {ReviewStatus.PENDING, ReviewStatus.IN_REVIEW}:
            hitl_service.supersede(review.id, reason)

    def _release_requirement_if_idle(self, solution) -> None:
        """没有其他待审项时，需求从审核中回到设计中。"""
        from ..models.review import ReviewStatus
        from .hitl_service import hitl_service

        if not self._requirement_service or self.has_pending_solution(solution.requirement_id):
            return
        requirement = self._requirement_service.get(solution.requirement_id)
        if requirement is None or requirement.status != RequirementStatus.REVIEWING:
            return
        still_open = any(
            item.requirement_id == requirement.id and item.status in {ReviewStatus.PENDING, ReviewStatus.IN_REVIEW}
            for item in hitl_service._review_items.values()
        )
        if still_open:
            return
        self._update_requirement_status(requirement, RequirementStatus.DESIGNING)

    def regenerate_solution(
        self,
        solution_id: UUID,
        additional_context: Optional[str] = None,
    ) -> Optional[Union[BugFixSolution, FeatureDesignSolution]]:
        """重新生成方案

        Args:
            solution_id: 原方案 ID
            additional_context: 额外上下文

        Returns:
            新生成的方案
        """
        old_solution = self._solutions.get(solution_id)
        if not old_solution:
            return None

        reason = "已重新生成，之前的方案作废"
        for solution in self._solutions_for(old_solution.requirement_id):
            if solution.status == SolutionStatus.IMPLEMENTED:
                continue
            if solution.id != old_solution.id and solution.status not in {
                SolutionStatus.DRAFT,
                SolutionStatus.PENDING_REVIEW,
            }:
                continue
            if solution.status == SolutionStatus.REJECTED:
                continue
            self._void_solution(solution, reason)

        return self.generate_solution(
            requirement_id=old_solution.requirement_id,
            force_regenerate=True,
            additional_context=additional_context,
        )

    def delete_solution(self, solution_id: UUID) -> bool:
        """删除方案

        Args:
            solution_id: 方案 ID

        Returns:
            是否删除成功
        """
        solution = self._solutions.get(solution_id)
        if not solution:
            return False

        requirement_id = solution.requirement_id
        if requirement_id in self._requirement_to_solutions:
            self._requirement_to_solutions[requirement_id] = [
                sid for sid in self._requirement_to_solutions[requirement_id]
                if sid != solution_id
            ]

        del self._solutions[solution_id]
        return True

    def delete_solutions_by_requirement(self, requirement_id: UUID) -> int:
        """删除需求下所有方案

        Args:
            requirement_id: 需求 ID

        Returns:
            删除的方案数量
        """
        solution_ids = self._requirement_to_solutions.get(requirement_id, [])
        count = 0

        for solution_id in solution_ids:
            if solution_id in self._solutions:
                del self._solutions[solution_id]
                count += 1

        if requirement_id in self._requirement_to_solutions:
            del self._requirement_to_solutions[requirement_id]

        return count

    def get_solution_statistics(self, requirement_id: Optional[UUID] = None) -> dict:
        """获取方案统计

        Args:
            requirement_id: 需求 ID（可选，不传则统计全部）

        Returns:
            统计数据
        """
        if requirement_id:
            solution_ids = self._requirement_to_solutions.get(requirement_id, [])
            solutions = [
                self._solutions[sid] for sid in solution_ids
                if sid in self._solutions
            ]
        else:
            solutions = list(self._solutions.values())

        by_type = {}
        for t in SolutionType:
            by_type[t.value] = len([s for s in solutions if s.type == t])

        by_status = {}
        for s in SolutionStatus:
            by_status[s.value] = len([sol for sol in solutions if sol.status == s])

        by_agent = {}
        for sol in solutions:
            agent = sol.created_by_agent or "unknown"
            by_agent[agent] = by_agent.get(agent, 0) + 1

        return {
            "total": len(solutions),
            "by_type": by_type,
            "by_status": by_status,
            "by_agent": by_agent,
        }


solution_service = SolutionService()
