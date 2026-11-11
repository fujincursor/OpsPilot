"""需求流程监控与推进控制。"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...models.requirement import Requirement
from ...services.project_service import project_service
from ...services.requirement_service import requirement_service
from ...services.workflow_service import workflow_service

router = APIRouter()


class WorkflowItem(BaseModel):
    """监控页上的一条需求。"""
    requirement_id: UUID
    title: str
    type: str
    status: str
    stage: str
    auto_advance: bool
    session_id: Optional[UUID] = None
    sandbox_profile: str = ""
    updated_at: Optional[str] = None
    current_agent: str = ""


class WorkflowBoard(BaseModel):
    """按阶段汇总的监控数据。"""
    running: int = 0
    pending_review: int = 0
    completed: int = 0
    closed: int = 0
    items: List[WorkflowItem] = Field(default_factory=list)


def _current_agent(stage: str, requirement_type: str, project_id: UUID) -> str:
    from ...models.agent import AgentType
    from ...services.agent_runtime import agent_runtime

    agent_type = {
        "分析": AgentType.LEAD,
        "编码": AgentType.CODE_GENERATION,
        "测试": AgentType.TEST_EXECUTION,
    }.get(stage)
    if stage == "方案":
        agent_type = AgentType.BUG_FIX if requirement_type == "bug" else AgentType.FEATURE_DESIGN
    if agent_type is not None:
        agent = agent_runtime.get(project_id, agent_type)
        if agent is not None:
            return agent.name if agent.enabled else f"{agent.name}（未启用）"
    return {
        "分析": "需求分析",
        "方案": "方案设计",
        "待审批": "人工审批",
        "编码": "代码生成",
        "测试": "测试执行",
        "完成": "已完成",
        "已关闭": "已停止",
        "已暂停": "已暂停",
    }.get(stage, "Lead Agent")


def _board(project_id: UUID) -> WorkflowBoard:
    requirements, _ = requirement_service.list(project_id, page=1, page_size=200)
    profile = workflow_service._sandbox_profile(project_id)
    items = [
        WorkflowItem(
            requirement_id=item.id,
            title=item.title,
            type=item.type.value,
            status=item.status.value,
            stage=workflow_service.stage_label(item),
            auto_advance=item.auto_advance,
            session_id=item.session_id,
            sandbox_profile=profile,
            updated_at=item.updated_at.isoformat() if item.updated_at else None,
            current_agent=_current_agent(workflow_service.stage_label(item), item.type.value, project_id),
        )
        for item in requirements
    ]
    return WorkflowBoard(
        running=sum(1 for item in items if item.stage in {"分析", "方案", "编码", "测试"}),
        pending_review=sum(1 for item in items if item.stage == "待审批"),
        completed=sum(1 for item in items if item.stage == "完成"),
        closed=sum(1 for item in items if item.stage == "已关闭"),
        items=items,
    )


@router.get("/projects/{project_id}/workflow", response_model=WorkflowBoard)
async def get_workflow_board(project_id: UUID) -> WorkflowBoard:
    """按需求阶段汇总执行情况。"""
    if not project_service.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return _board(project_id)


@router.post("/requirements/{requirement_id}/workflow/pause", response_model=Requirement)
async def pause_workflow(requirement_id: UUID) -> Requirement:
    """停止自动推进，保留当前阶段。"""
    requirement = workflow_service.pause(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.post("/requirements/{requirement_id}/workflow/resume", response_model=Requirement)
async def resume_workflow(requirement_id: UUID) -> Requirement:
    """恢复自动推进。"""
    requirement = await workflow_service.resume(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.post("/requirements/{requirement_id}/workflow/stop", response_model=Requirement)
async def stop_workflow(requirement_id: UUID) -> Requirement:
    """终止需求，不再继续编码或测试。"""
    requirement = workflow_service.stop(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement
