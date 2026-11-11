"""需求管理 API"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...models.requirement import (
    Requirement,
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
    RequirementType,
    RequirementStatus,
    RequirementPriority,
    RequirementFilters,
    RequirementStatusUpdate,
    RequirementAssignUpdate,
    RequirementAnalysis,
    RequirementAnalyzeRequest,
)
from ...services.requirement_service import requirement_service
from ...services.lead_agent_service import lead_agent_service
from ...services.project_service import project_service
from ...services.workflow_service import workflow_service

router = APIRouter()


@router.post("/projects/{project_id}/requirements", response_model=Requirement, status_code=201)
async def create_requirement(
    project_id: UUID,
    data: RequirementCreate
) -> Requirement:
    """
    提交新需求

    自动调用 Lead Agent 分析需求文本，提取类型、优先级和关键词。
    如果请求中指定了 type 或 priority，则使用指定的值而非 AI 分析结果。

    - **title**: 需求标题 (必填, 1-200字符)
    - **description**: 需求详细描述 (必填, 1-5000字符)
    - **source**: 需求来源 (可选, 默认 web)
    - **type**: 需求类型 (可选，不填则自动分析)
    - **priority**: 优先级 (可选，不填则自动分析)
    """
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    blocked = workflow_service.knowledge_block(project_id)
    if blocked:
        raise HTTPException(
            status_code=428,
            detail={
                "message": blocked.message,
                "project_id": str(project_id),
            },
        )

    requirement = requirement_service.create(project_id, data)
    if requirement.type != RequirementType.QUESTION:
        try:
            await workflow_service.open_solution_review(requirement)
        except Exception:
            requirement = requirement_service.get(requirement.id) or requirement
        else:
            requirement = requirement_service.get(requirement.id) or requirement
    return requirement


@router.get("/projects/{project_id}/requirements", response_model=RequirementResponse)
async def list_requirements(
    project_id: UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[RequirementType] = Query(None, description="需求类型筛选"),
    status: Optional[RequirementStatus] = Query(None, description="状态筛选"),
    priority: Optional[RequirementPriority] = Query(None, description="优先级筛选"),
    assignee: Optional[str] = Query(None, description="分配人筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索")
) -> RequirementResponse:
    """
    获取项目需求列表

    支持分页和多种筛选条件。
    """
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    filters = RequirementFilters(
        type=type,
        status=status,
        priority=priority,
        assignee=assignee,
        keyword=keyword
    )

    items, total = requirement_service.list(
        project_id=project_id,
        filters=filters,
        page=page,
        page_size=page_size
    )

    return RequirementResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/projects/{project_id}/requirements/statistics")
async def get_requirement_statistics(project_id: UUID) -> dict:
    """
    获取项目需求统计

    返回按类型、状态、优先级分组的统计数据。
    """
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return requirement_service.get_statistics(project_id)


@router.get("/requirements/{requirement_id}", response_model=Requirement)
async def get_requirement(requirement_id: UUID) -> Requirement:
    """获取单个需求详情"""
    requirement = requirement_service.get(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.put("/requirements/{requirement_id}", response_model=Requirement)
async def update_requirement(
    requirement_id: UUID,
    data: RequirementUpdate
) -> Requirement:
    """
    更新需求信息

    如果更新了标题或描述，会重新进行 AI 分析以更新关键词。
    """
    requirement = requirement_service.update(requirement_id, data)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.patch("/requirements/{requirement_id}/status", response_model=Requirement)
async def update_requirement_status(
    requirement_id: UUID,
    data: RequirementStatusUpdate
) -> Requirement:
    """
    更新需求状态

    状态流转：pending -> analyzing -> designing -> reviewing -> coding -> testing -> completed -> closed
    """
    current = requirement_service.get(requirement_id)
    if not current:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if current.type == RequirementType.QUESTION and data.status in {
        RequirementStatus.DESIGNING,
        RequirementStatus.REVIEWING,
        RequirementStatus.CODING,
        RequirementStatus.TESTING,
    }:
        raise HTTPException(status_code=400, detail="咨询类需求不进入方案、编码或测试")
    previous = current.status
    requirement = requirement_service.update_status(requirement_id, data.status)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if data.status in {
        RequirementStatus.PENDING,
        RequirementStatus.ANALYZING,
        RequirementStatus.DESIGNING,
    }:
        from ...services.solution_service import solution_service

        solution_service.align_with_requirement(requirement_id)
    elif data.status == RequirementStatus.REVIEWING and previous != RequirementStatus.REVIEWING:
        workflow_service.submit_solution_for_requirement(requirement)
    return requirement


@router.patch("/requirements/{requirement_id}/assign", response_model=Requirement)
async def assign_requirement(
    requirement_id: UUID,
    data: RequirementAssignUpdate
) -> Requirement:
    """
    分配需求

    将需求分配给指定人员处理。如果需求状态为 pending，会自动更新为 analyzing。
    """
    requirement = requirement_service.assign(requirement_id, data.assignee)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.delete("/requirements/{requirement_id}", status_code=204)
async def delete_requirement(requirement_id: UUID):
    """删除需求"""
    if not requirement_service.delete(requirement_id):
        raise HTTPException(status_code=404, detail="Requirement not found")


@router.post("/requirements/analyze", response_model=RequirementAnalysis)
async def analyze_requirement_text(data: RequirementAnalyzeRequest) -> RequirementAnalysis:
    """
    分析需求文本（调试用）

    直接调用 Lead Agent 分析文本，返回识别的类型、建议的优先级和提取的关键词。
    可用于测试和调试 AI 分析功能。
    """
    if data.project_id:
        analysis = requirement_service._analyze_with_lead(data.project_id, data.text)
        if analysis is None:
            raise HTTPException(status_code=409, detail="Lead Agent 未启用，这一阶段不会执行")
        return analysis
    return lead_agent_service.analyze_requirement(data.text)
