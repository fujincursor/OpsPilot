"""技能说明 API。"""

from fastapi import APIRouter, HTTPException

from ...services.skill_catalog import SkillDocument, SkillNotFoundError, read_skill

router = APIRouter()


@router.get("/{skill_key}", response_model=SkillDocument)
async def get_skill(skill_key: str) -> SkillDocument:
    """读取内置技能的说明正文。"""
    try:
        return read_skill(skill_key)
    except SkillNotFoundError:
        raise HTTPException(status_code=404, detail="技能说明不存在")
