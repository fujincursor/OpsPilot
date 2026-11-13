"""空库时写入测试用户、技能目录和 Agent 默认提示。已有记录不覆盖。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models.project import default_project_skills
from .schema import AgentPromptTemplateRow, SkillCatalogRow, UserRow

_PROMPTS = {
    "lead": """你是运维 Agent 生产系统的 Lead Agent。
你的职责是理解用户提交的运维需求或 Bug，检索项目上下文，完成分类，并委派给合适的 Sub-Agent，最后整合结果。

分类规则：
- Bug：系统故障、错误、异常行为
- 新需求：功能增强、新特性、优化建议

输出时说明分类依据、委派对象，以及需要 Sub-Agent 完成的任务。""",
    "bugfix": """你是 Bug 修复专家 Agent。
负责分析 Bug 根因，定位问题代码，并生成可执行的修复方案。

修复方案必须包含：
1. 问题定位
2. 根因分析
3. 具体修改建议
4. 影响范围评估
5. 测试与回滚建议""",
    "feature": """你是新需求设计专家 Agent。
负责分析需求，设计技术方案，并定义接口和模块划分。

设计方案必须包含：
1. 功能概述和用户故事
2. 功能范围
3. 技术架构
4. 接口与数据模型
5. 实施计划与风险""",
    "codegen": """你是代码生成专家 Agent。
根据已通过的设计方案生成代码，并做语法检查。

输出必须包含：
1. 代码文件列表和内容
2. 变更说明
3. 语法与质量检查结果""",
    "test": """你是测试执行专家 Agent。
负责生成测试用例，在沙箱中执行测试，并给出测试报告。

输出必须包含：
1. 测试结果汇总
2. 失败用例分析
3. 覆盖率
4. 建议的下一步""",
}

_USERS = (
    ("admin-001", "admin", "admin@opspilot.example.com", "admin", "admin123"),
    ("operator-001", "operator", "operator@opspilot.example.com", "operator", "operator123"),
    ("reviewer-001", "reviewer", "reviewer@opspilot.example.com", "reviewer", "reviewer123"),
    ("viewer-001", "viewer", "viewer@opspilot.example.com", "viewer", "viewer123"),
)


def seed_if_empty(engine) -> None:
    with Session(engine) as db:
        _seed_users(db)
        _seed_skills(db)
        _seed_prompts(db)
        db.commit()


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _seed_users(db: Session) -> None:
    if _count(db, UserRow):
        return
    now = datetime.utcnow()
    for user_id, username, email, role, password in _USERS:
        db.add(UserRow(
            id=user_id,
            username=username,
            email=email,
            role=role,
            hashed_password=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            is_active=True,
            created_at=now,
            updated_at=None,
        ))


def _seed_skills(db: Session) -> None:
    if _count(db, SkillCatalogRow):
        return
    defaults = {item.key: item for item in default_project_skills()}
    root = Path(__file__).resolve().parents[2] / "skills" / "opspilot"
    if not root.is_dir():
        return
    for path in sorted(root.iterdir()):
        skill_file = path / "SKILL.md"
        if not skill_file.is_file():
            continue
        name, description, content = _split_skill(skill_file.read_text(encoding="utf-8"), path.name)
        preset = defaults.get(path.name)
        db.add(SkillCatalogRow(
            skill_key=path.name,
            name=preset.name if preset else name,
            description=description or (preset.description if preset else ""),
            agent=preset.agent if preset else "",
            content=content,
        ))


def _split_skill(text: str, fallback_name: str) -> tuple[str, str, str]:
    name = fallback_name
    description = ""
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            header = text[3:end]
            body = text[end + 4:].lstrip("\n")
            for line in header.splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip() or name
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
    return name, description, body.strip()


def _seed_prompts(db: Session) -> None:
    if _count(db, AgentPromptTemplateRow):
        return
    for agent_type, prompt in _PROMPTS.items():
        db.add(AgentPromptTemplateRow(agent_type=agent_type, prompt=prompt))
