"""测试 API"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from ...models.test import (
    TestTask,
    TestTaskCreate,
    TestTaskResponse,
    TestStatus,
    TestCase,
    TestCaseType,
    TestResult,
    TestReport,
    TestRerunRequest,
    TestReviewSubmitRequest,
    CITriggerRequest,
    CIPipelineInfo,
    TestFilters,
)
from ...services.test_service import test_service
from ...services.codegen_service import codegen_service

router = APIRouter()


@router.post(
    "/codegen/{task_id}/tests",
    response_model=TestTask,
    status_code=201,
)
async def create_test_task(
    task_id: UUID,
    data: Optional[TestTaskCreate] = None,
    background_tasks: BackgroundTasks = None,
) -> TestTask:
    """
    创建测试任务

    为代码生成任务创建测试任务，任务将在后台执行测试生成和运行。

    - **task_id**: 代码生成任务 ID
    - **additional_context**: 额外上下文（可选）
    - **test_types**: 要生成的测试类型（可选，默认 unit）
    """
    codegen_task = codegen_service.get_task(task_id)
    if not codegen_task:
        raise HTTPException(status_code=404, detail="Code generation task not found")

    if codegen_task.status.value != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot create test task. Code generation task status: {codegen_task.status.value}"
        )

    test_task = test_service.create_test_task(
        codegen_task_id=task_id,
        data=data,
    )

    if not test_task:
        raise HTTPException(
            status_code=500, detail="Failed to create test task"
        )

    test_types = data.test_types if data and data.test_types else [TestCaseType.UNIT]

    if background_tasks:
        background_tasks.add_task(
            _execute_test_task,
            test_task.id,
            test_types,
        )

    return test_task


async def _execute_test_task(task_id: UUID, test_types: List[TestCaseType]):
    """后台执行测试任务"""
    await test_service.generate_and_run_tests(task_id, test_types)


@router.get(
    "/tests/{test_task_id}",
    response_model=TestTask,
)
async def get_test_task(
    test_task_id: UUID,
) -> TestTask:
    """
    获取测试任务状态

    返回任务的完整信息，包括：
    - 任务状态 (pending/generating/running/completed/failed)
    - 测试用例列表
    - 测试结果列表
    - 覆盖率信息

    - **test_task_id**: 测试任务 ID
    """
    task = test_service.get_task(test_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Test task not found")
    return task


@router.get(
    "/tests/{test_task_id}/cases",
    response_model=List[TestCase],
)
async def get_test_cases(
    test_task_id: UUID,
) -> List[TestCase]:
    """
    获取测试用例列表

    返回任务生成的所有测试用例。

    - **test_task_id**: 测试任务 ID
    """
    cases = test_service.get_test_cases(test_task_id)
    if cases is None:
        raise HTTPException(status_code=404, detail="Test task not found")
    return cases


@router.get(
    "/tests/{test_task_id}/results",
    response_model=List[TestResult],
)
async def get_test_results(
    test_task_id: UUID,
) -> List[TestResult]:
    """
    获取测试结果

    返回所有测试用例的执行结果。

    - **test_task_id**: 测试任务 ID
    """
    results = test_service.get_test_results(test_task_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Test task not found")
    return results


@router.get(
    "/tests/{test_task_id}/report",
    response_model=TestReport,
)
async def get_test_report(
    test_task_id: UUID,
) -> TestReport:
    """
    获取测试报告

    返回测试的完整报告，包括：
    - 通过/失败/跳过数量
    - 代码覆盖率
    - 执行耗时
    - 失败用例列表

    - **test_task_id**: 测试任务 ID
    """
    task = test_service.get_task(test_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Test task not found")

    if task.status != TestStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Test report not available yet. Task status: {task.status.value}"
        )

    report = test_service.get_test_report(test_task_id)
    if not report:
        raise HTTPException(status_code=404, detail="Test report not found")

    return report


@router.post(
    "/tests/{test_task_id}/rerun",
    response_model=TestTask,
)
async def rerun_tests(
    test_task_id: UUID,
    data: Optional[TestRerunRequest] = None,
    background_tasks: BackgroundTasks = None,
) -> TestTask:
    """
    重新运行测试

    可以：
    - 重新运行所有测试
    - 指定要重新运行的测试用例
    - 尝试修复失败的测试

    - **test_task_id**: 测试任务 ID
    - **test_case_ids**: 指定要重新运行的测试用例 ID（可选）
    - **fix_failed_tests**: 是否尝试修复失败的测试（默认 false）
    """
    task = test_service.get_task(test_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Test task not found")

    test_case_ids = data.test_case_ids if data else None
    fix_failed_tests = data.fix_failed_tests if data else False

    if background_tasks:
        background_tasks.add_task(
            _execute_rerun,
            test_task_id,
            test_case_ids,
            fix_failed_tests,
        )
        task.status = TestStatus.PENDING
        return task
    else:
        result = await test_service.rerun_tests(
            task_id=test_task_id,
            test_case_ids=test_case_ids,
            fix_failed_tests=fix_failed_tests,
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to rerun tests")

        return result


async def _execute_rerun(
    task_id: UUID,
    test_case_ids: Optional[List[UUID]],
    fix_failed_tests: bool,
):
    """后台执行测试重新运行"""
    await test_service.rerun_tests(
        task_id=task_id,
        test_case_ids=test_case_ids,
        fix_failed_tests=fix_failed_tests,
    )


@router.post(
    "/tests/{test_task_id}/submit-review",
    response_model=TestTask,
)
async def submit_test_review(
    test_task_id: UUID,
    data: Optional[TestReviewSubmitRequest] = None,
) -> TestTask:
    """
    提交测试审核

    将测试结果提交审核。

    - **test_task_id**: 测试任务 ID
    - **reviewer_notes**: 审核备注（可选）
    - **approve_with_failures**: 是否允许带失败用例提交（默认 false）
    """
    task = test_service.get_task(test_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Test task not found")

    if task.status != TestStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit for review. Task status: {task.status.value}"
        )

    reviewer_notes = data.reviewer_notes if data else None
    approve_with_failures = data.approve_with_failures if data else False

    result = test_service.submit_test_review(
        task_id=test_task_id,
        reviewer_notes=reviewer_notes,
        approve_with_failures=approve_with_failures,
    )

    if not result:
        report = test_service.get_test_report(test_task_id)
        if report and report.failed > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit with {report.failed} failed tests. Set approve_with_failures=true to override."
            )
        raise HTTPException(status_code=500, detail="Failed to submit for review")

    return result


@router.post(
    "/tests/{test_task_id}/trigger-ci",
    response_model=CIPipelineInfo,
)
async def trigger_ci_pipeline(
    test_task_id: UUID,
    data: Optional[CITriggerRequest] = None,
) -> CIPipelineInfo:
    """
    触发 CI 流水线

    为完成的测试任务触发 CI/CD 流水线。

    - **test_task_id**: 测试任务 ID
    - **target_branch**: 目标分支（默认 main）
    - **run_full_suite**: 是否运行完整测试套件（默认 false）
    - **extra_args**: 额外参数（可选）
    """
    task = test_service.get_task(test_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Test task not found")

    if task.status != TestStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot trigger CI. Task status: {task.status.value}"
        )

    target_branch = data.target_branch if data else "main"
    run_full_suite = data.run_full_suite if data else False
    extra_args = data.extra_args if data else None

    pipeline_info = test_service.trigger_ci_pipeline(
        task_id=test_task_id,
        target_branch=target_branch,
        run_full_suite=run_full_suite,
        extra_args=extra_args,
    )

    if not pipeline_info:
        raise HTTPException(status_code=500, detail="Failed to trigger CI pipeline")

    return pipeline_info


@router.get(
    "/tests/{test_task_id}/ci-status",
    response_model=CIPipelineInfo,
)
async def get_ci_pipeline_status(
    test_task_id: UUID,
) -> CIPipelineInfo:
    """
    获取 CI 流水线状态

    返回 CI 流水线的当前状态。

    - **test_task_id**: 测试任务 ID
    """
    pipeline_info = test_service.get_ci_pipeline_status(test_task_id)
    if not pipeline_info:
        raise HTTPException(status_code=404, detail="CI pipeline not found")
    return pipeline_info


@router.get(
    "/tests",
    response_model=TestTaskResponse,
)
async def list_test_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[TestStatus] = Query(None, description="状态筛选"),
    codegen_task_id: Optional[UUID] = Query(None, description="代码生成任务筛选"),
    requirement_id: Optional[UUID] = Query(None, description="需求筛选"),
) -> TestTaskResponse:
    """
    获取测试任务列表

    - **page**: 页码
    - **page_size**: 每页数量
    - **status**: 状态筛选
    - **codegen_task_id**: 代码生成任务筛选
    - **requirement_id**: 需求筛选
    """
    filters = TestFilters(
        status=status,
        codegen_task_id=codegen_task_id,
        requirement_id=requirement_id,
    )

    tasks = test_service.list_tasks(
        filters=filters,
        page=page,
        page_size=page_size,
    )

    total = test_service.count_tasks(filters)

    return TestTaskResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/tests/{test_task_id}", status_code=204)
async def delete_test_task(test_task_id: UUID):
    """
    删除测试任务

    同时会清理关联的沙箱环境。

    - **test_task_id**: 测试任务 ID
    """
    if not test_service.delete_task(test_task_id):
        raise HTTPException(status_code=404, detail="Test task not found")


@router.get("/tests/statistics")
async def get_test_statistics(
    codegen_task_id: Optional[UUID] = Query(None, description="代码生成任务 ID（可选）"),
) -> dict:
    """
    获取测试统计

    返回测试任务统计数据，包括：
    - 按状态分组的任务数
    - 测试用例通过/失败/跳过数
    - 平均覆盖率
    - CI 触发数

    - **codegen_task_id**: 代码生成任务 ID（可选，不传则统计全部）
    """
    return test_service.get_statistics(codegen_task_id)
