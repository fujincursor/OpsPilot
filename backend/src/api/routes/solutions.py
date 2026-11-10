"""方案管理 API"""

from typing import Optional, Union
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...models.solution import (
    Solution,
    BugFixSolution,
    FeatureDesignSolution,
    SolutionResponse,
    SolutionUpdate,
    SolutionStatusUpdate,
    SolutionGenerateRequest,
    SolutionType,
    SolutionStatus,
    SolutionFilters,
)
from ...services.solution_service import solution_service
from ...services.requirement_service import requirement_service

router = APIRouter()


@router.post(
    "/requirements/{requirement_id}/solutions/generate",
    response_model=Union[BugFixSolution, FeatureDesignSolution],
    status_code=201,
)
async def generate_solution(
    requirement_id: UUID,
    data: Optional[SolutionGenerateRequest] = None,
) -> Union[BugFixSolution, FeatureDesignSolution]:
    """
    为需求生成方案

    根据需求类型自动调用对应的 Agent 生成方案：
    - Bug 类型需求：调用 BugFixAgent 生成修复方案
    - Feature 类型需求：调用 FeatureDesignAgent 生成设计方案

    如果需求已有草稿方案且未设置 force_regenerate，则返回现有方案。

    - **requirement_id**: 需求 ID
    - **force_regenerate**: 是否强制重新生成（可选，默认 false）
    - **additional_context**: 额外上下文信息（可选）
    """
    requirement = requirement_service.get(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    force_regenerate = data.force_regenerate if data else False
    additional_context = data.additional_context if data else None

    solution = solution_service.generate_solution(
        requirement_id=requirement_id,
        force_regenerate=force_regenerate,
        additional_context=additional_context,
    )

    if not solution:
        raise HTTPException(
            status_code=500, detail="Failed to generate solution"
        )

    return solution


@router.get(
    "/requirements/{requirement_id}/solutions",
    response_model=SolutionResponse,
)
async def list_solutions(
    requirement_id: UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[SolutionType] = Query(None, description="方案类型筛选"),
    status: Optional[SolutionStatus] = Query(None, description="状态筛选"),
    created_by_agent: Optional[str] = Query(None, description="创建 Agent 筛选"),
) -> SolutionResponse:
    """
    获取需求的方案列表

    支持分页和多种筛选条件。

    - **requirement_id**: 需求 ID
    - **page**: 页码
    - **page_size**: 每页数量
    - **type**: 方案类型筛选 (bugfix/feature_design)
    - **status**: 状态筛选 (draft/pending_review/approved/rejected/implemented)
    - **created_by_agent**: 创建 Agent 筛选
    """
    requirement = requirement_service.get(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    filters = SolutionFilters(
        type=type,
        status=status,
        created_by_agent=created_by_agent,
    )

    solutions = solution_service.get_solutions_by_requirement(
        requirement_id=requirement_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    total = solution_service.count_solutions_by_requirement(
        requirement_id=requirement_id,
        filters=filters,
    )

    return SolutionResponse(
        items=solutions,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/solutions/{solution_id}",
    response_model=Union[Solution, BugFixSolution, FeatureDesignSolution],
)
async def get_solution(
    solution_id: UUID,
) -> Union[Solution, BugFixSolution, FeatureDesignSolution]:
    """
    获取方案详情

    返回方案的完整信息，包括：
    - 基础信息：标题、内容、状态、影响分析
    - Bug 修复方案额外包含：根因分析、修复步骤、回归风险
    - 功能设计方案额外包含：架构设计、API 设计、数据库变更

    - **solution_id**: 方案 ID
    """
    solution = solution_service.get_solution(solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    return solution


@router.put(
    "/solutions/{solution_id}",
    response_model=Union[Solution, BugFixSolution, FeatureDesignSolution],
)
async def update_solution(
    solution_id: UUID,
    data: SolutionUpdate,
) -> Union[Solution, BugFixSolution, FeatureDesignSolution]:
    """
    更新方案

    可更新方案的标题、内容、影响分析和受影响文件。
    状态更新请使用 PATCH /solutions/{solution_id}/status 接口。

    - **solution_id**: 方案 ID
    - **title**: 方案标题（可选）
    - **content**: 方案内容（可选）
    - **impact_analysis**: 影响分析（可选）
    - **affected_files**: 受影响文件列表（可选）
    """
    solution = solution_service.update_solution(solution_id, data)
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    return solution


@router.patch(
    "/solutions/{solution_id}/status",
    response_model=Union[Solution, BugFixSolution, FeatureDesignSolution],
)
async def update_solution_status(
    solution_id: UUID,
    data: SolutionStatusUpdate,
) -> Union[Solution, BugFixSolution, FeatureDesignSolution]:
    """方案通过、拒绝和完成只能由审核决定推进。"""
    if data.status in {SolutionStatus.APPROVED, SolutionStatus.REJECTED, SolutionStatus.IMPLEMENTED}:
        raise HTTPException(status_code=409, detail="方案状态只能通过审核决定变更")
    solution = solution_service.update_solution_status(
        solution_id=solution_id,
        status=data.status,
        review_comment=data.review_comment,
    )

    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    return solution


@router.post(
    "/solutions/{solution_id}/regenerate",
    response_model=Union[BugFixSolution, FeatureDesignSolution],
    status_code=201,
)
async def regenerate_solution(
    solution_id: UUID,
    data: Optional[SolutionGenerateRequest] = None,
) -> Union[BugFixSolution, FeatureDesignSolution]:
    """
    重新生成方案

    将原方案标记为已拒绝，并基于同一需求重新生成新方案。
    可提供额外上下文信息以改进生成结果。

    - **solution_id**: 原方案 ID
    - **additional_context**: 额外上下文信息（可选）
    """
    old_solution = solution_service.get_solution(solution_id)
    if not old_solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    additional_context = data.additional_context if data else None

    new_solution = solution_service.regenerate_solution(
        solution_id=solution_id,
        additional_context=additional_context,
    )

    if not new_solution:
        raise HTTPException(
            status_code=500, detail="Failed to regenerate solution"
        )

    return new_solution


@router.delete("/solutions/{solution_id}", status_code=204)
async def delete_solution(solution_id: UUID):
    """
    删除方案

    - **solution_id**: 方案 ID
    """
    if not solution_service.delete_solution(solution_id):
        raise HTTPException(status_code=404, detail="Solution not found")


@router.get("/solutions/statistics")
async def get_solution_statistics(
    requirement_id: Optional[UUID] = Query(None, description="需求 ID（可选）"),
) -> dict:
    """
    获取方案统计

    返回按类型、状态、创建 Agent 分组的统计数据。
    如果提供 requirement_id，则只统计该需求下的方案。

    - **requirement_id**: 需求 ID（可选）
    """
    return solution_service.get_solution_statistics(requirement_id)
