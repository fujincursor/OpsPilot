"""代码生成 API"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from ...models.codegen import (
    CodeGenTask,
    CodeGenTaskCreate,
    CodeGenTaskResponse,
    CodeGenStatus,
    CodeFile,
    LintResult,
    CodeDiff,
    MergeRequestInfo,
    CodeGenRegenerateRequest,
    CodeReviewSubmitRequest,
    CodeGenFilters,
)
from ...services.codegen_service import codegen_service
from ...services.solution_service import solution_service

router = APIRouter()


@router.post(
    "/solutions/{solution_id}/codegen",
    response_model=CodeGenTask,
    status_code=201,
)
async def create_codegen_task(
    solution_id: UUID,
    data: Optional[CodeGenTaskCreate] = None,
    background_tasks: BackgroundTasks = None,
) -> CodeGenTask:
    """
    创建代码生成任务

    根据方案创建代码生成任务，任务将在后台执行代码生成和 Lint 检查。

    - **solution_id**: 方案 ID
    - **language**: 主要编程语言（可选，默认 python）
    - **additional_context**: 额外上下文（可选）
    """
    solution = solution_service.get_solution(solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    language = data.language if data else "python"
    additional_context = data.additional_context if data and hasattr(data, 'additional_context') else None

    task = codegen_service.create_codegen_task(
        solution_id=solution_id,
        language=language,
        additional_context=additional_context,
    )

    if not task:
        raise HTTPException(
            status_code=500, detail="Failed to create code generation task"
        )

    if background_tasks:
        background_tasks.add_task(
            _execute_codegen_task,
            task.id,
        )

    return task


async def _execute_codegen_task(task_id: UUID):
    """后台执行代码生成任务"""
    await codegen_service.generate_and_lint(task_id)


@router.get(
    "/codegen/{task_id}",
    response_model=CodeGenTask,
)
async def get_codegen_task(
    task_id: UUID,
) -> CodeGenTask:
    """
    获取代码生成任务状态

    返回任务的完整信息，包括：
    - 任务状态 (pending/generating/linting/completed/failed)
    - 生成的文件列表
    - Lint 检查结果
    - MR 信息（如已创建）

    - **task_id**: 任务 ID
    """
    task = codegen_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Code generation task not found")
    return task


@router.get(
    "/codegen/{task_id}/files",
    response_model=List[CodeFile],
)
async def get_codegen_files(
    task_id: UUID,
) -> List[CodeFile]:
    """
    获取生成的文件列表

    返回任务生成的所有代码文件，包括文件路径、内容、语言和操作类型。

    - **task_id**: 任务 ID
    """
    files = codegen_service.get_files(task_id)
    if files is None:
        raise HTTPException(status_code=404, detail="Code generation task not found")
    return files


@router.get(
    "/codegen/{task_id}/diff",
    response_model=List[CodeDiff],
)
async def get_code_diff(
    task_id: UUID,
) -> List[CodeDiff]:
    """
    获取代码 diff

    返回任务生成的代码与原代码的差异，使用 unified diff 格式。

    - **task_id**: 任务 ID
    """
    diffs = codegen_service.get_code_diff(task_id)
    if diffs is None:
        raise HTTPException(status_code=404, detail="Code generation task not found")
    return diffs


@router.get(
    "/codegen/{task_id}/lint",
    response_model=LintResult,
)
async def get_lint_result(
    task_id: UUID,
) -> LintResult:
    """
    获取 Lint 检查结果

    返回代码的语法检查结果，包括：
    - 是否通过
    - 错误列表
    - 警告列表

    - **task_id**: 任务 ID
    """
    task = codegen_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Code generation task not found")

    if not task.lint_result:
        raise HTTPException(
            status_code=400,
            detail="Lint result not available yet. Task status: " + task.status.value
        )

    return task.lint_result


@router.post(
    "/codegen/{task_id}/regenerate",
    response_model=CodeGenTask,
)
async def regenerate_code(
    task_id: UUID,
    data: Optional[CodeGenRegenerateRequest] = None,
    background_tasks: BackgroundTasks = None,
) -> CodeGenTask:
    """
    重新生成代码

    可以：
    - 重新生成所有文件
    - 指定要重新生成的文件
    - 基于 Lint 错误自动修复

    - **task_id**: 任务 ID
    - **files_to_regenerate**: 指定要重新生成的文件路径列表（可选）
    - **fix_lint_errors**: 是否基于 lint 错误修复（默认 true）
    - **additional_instructions**: 额外指令（可选）
    """
    task = codegen_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Code generation task not found")

    files_to_regenerate = data.files_to_regenerate if data else None
    fix_lint_errors = data.fix_lint_errors if data else True
    additional_instructions = data.additional_instructions if data else None

    if background_tasks:
        background_tasks.add_task(
            _execute_regenerate,
            task_id,
            files_to_regenerate,
            fix_lint_errors,
            additional_instructions,
        )
        task.status = CodeGenStatus.PENDING
        return task
    else:
        result = await codegen_service.regenerate_code(
            task_id=task_id,
            files_to_regenerate=files_to_regenerate,
            fix_lint_errors=fix_lint_errors,
            additional_instructions=additional_instructions,
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to regenerate code")

        return result


async def _execute_regenerate(
    task_id: UUID,
    files_to_regenerate: Optional[List[str]],
    fix_lint_errors: bool,
    additional_instructions: Optional[str],
):
    """后台执行代码重新生成"""
    await codegen_service.regenerate_code(
        task_id=task_id,
        files_to_regenerate=files_to_regenerate,
        fix_lint_errors=fix_lint_errors,
        additional_instructions=additional_instructions,
    )


@router.post(
    "/codegen/{task_id}/submit-review",
    response_model=CodeGenTask,
)
async def submit_for_review(
    task_id: UUID,
    data: Optional[CodeReviewSubmitRequest] = None,
) -> CodeGenTask:
    """
    提交代码审核

    将生成的代码提交审核，会自动创建 Merge Request。

    - **task_id**: 任务 ID
    - **reviewer_notes**: 审核备注（可选）
    - **auto_merge**: 是否自动合并（默认 false）
    """
    task = codegen_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Code generation task not found")

    if task.status != CodeGenStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit for review. Task status: {task.status.value}"
        )

    reviewer_notes = data.reviewer_notes if data else None
    auto_merge = data.auto_merge if data else False

    result = codegen_service.submit_for_review(
        task_id=task_id,
        reviewer_notes=reviewer_notes,
        auto_merge=auto_merge,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to submit for review")

    return result


@router.post(
    "/codegen/{task_id}/create-mr",
    response_model=MergeRequestInfo,
)
async def create_merge_request(
    task_id: UUID,
    title: Optional[str] = Query(None, description="MR 标题"),
    target_branch: str = Query("main", description="目标分支"),
) -> MergeRequestInfo:
    """
    创建 Merge Request

    为完成的代码生成任务创建 MR。

    - **task_id**: 任务 ID
    - **title**: MR 标题（可选，默认使用方案标题）
    - **target_branch**: 目标分支（默认 main）
    """
    task = codegen_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Code generation task not found")

    if task.status != CodeGenStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot create MR. Task status: {task.status.value}"
        )

    mr_info = codegen_service.create_merge_request(
        task_id=task_id,
        title=title,
        target_branch=target_branch,
    )

    if not mr_info:
        raise HTTPException(status_code=500, detail="Failed to create merge request")

    return mr_info


@router.get(
    "/solutions/{solution_id}/codegen/tasks",
    response_model=CodeGenTaskResponse,
)
async def list_codegen_tasks(
    solution_id: UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[CodeGenStatus] = Query(None, description="状态筛选"),
    language: Optional[str] = Query(None, description="语言筛选"),
) -> CodeGenTaskResponse:
    """
    获取方案的代码生成任务列表

    - **solution_id**: 方案 ID
    - **page**: 页码
    - **page_size**: 每页数量
    - **status**: 状态筛选
    - **language**: 语言筛选
    """
    solution = solution_service.get_solution(solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    filters = CodeGenFilters(
        status=status,
        language=language,
    )

    tasks = codegen_service.get_tasks_by_solution(
        solution_id=solution_id,
        filters=filters,
    )

    start = (page - 1) * page_size
    end = start + page_size
    paginated_tasks = tasks[start:end]

    return CodeGenTaskResponse(
        items=paginated_tasks,
        total=len(tasks),
        page=page,
        page_size=page_size,
    )


@router.delete("/codegen/{task_id}", status_code=204)
async def delete_codegen_task(task_id: UUID):
    """
    删除代码生成任务

    同时会清理关联的沙箱环境。

    - **task_id**: 任务 ID
    """
    if not codegen_service.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Code generation task not found")


@router.get("/codegen/statistics")
async def get_codegen_statistics(
    solution_id: Optional[UUID] = Query(None, description="方案 ID（可选）"),
) -> dict:
    """
    获取代码生成统计

    返回按状态、语言分组的统计数据，以及 Lint 通过率和 MR 创建数。

    - **solution_id**: 方案 ID（可选，不传则统计全部）
    """
    return codegen_service.get_statistics(solution_id)
