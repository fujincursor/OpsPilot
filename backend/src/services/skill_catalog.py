"""读取 skills/opspilot 下的技能说明。"""

import re
from pathlib import Path

from pydantic import BaseModel

_KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SKILL_ROOT = Path(__file__).resolve().parents[3] / "skills" / "opspilot"


class SkillDocument(BaseModel):
    """一份可展示的技能说明。"""
    key: str
    name: str
    description: str = ""
    content: str


class SkillNotFoundError(LookupError):
    """技能键不存在，或目录里没有对应的说明文档。"""


def read_skill(key: str) -> SkillDocument:
    """按技能键读取 SKILL.md，并去掉前置元数据。"""
    if not _KEY_PATTERN.fullmatch(key):
        raise SkillNotFoundError(key)
    path = (_SKILL_ROOT / key / "SKILL.md").resolve()
    if path.parent != (_SKILL_ROOT / key).resolve() or not path.is_file():
        raise SkillNotFoundError(key)

    text = path.read_text(encoding="utf-8")
    name, description, content = _split_frontmatter(text, fallback_name=key)
    return SkillDocument(key=key, name=name, description=description, content=content)


def _split_frontmatter(text: str, fallback_name: str) -> tuple[str, str, str]:
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
