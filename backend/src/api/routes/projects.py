"""项目管理 API"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...models.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectStatus
)
from ...services.project_service import project_service

router = APIRouter()


@router.get("", response_model=ProjectResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[ProjectStatus] = Query(None, description="项目状态筛选")
) -> ProjectResponse:
    """
    获取项目列表

    支持分页和状态筛选
    """
    items, total = project_service.list(page=page, page_size=page_size, status=status)
    return ProjectResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID) -> Project:
    """获取单个项目详情"""
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=Project, status_code=201)
async def create_project(data: ProjectCreate) -> Project:
    """
    创建新项目

    - **name**: 项目名称 (必填, 1-100字符)
    - **description**: 项目描述 (可选, 最多500字符)
    - **repo_url**: 代码仓库地址 (可选)
    """
    return project_service.create(data)


@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: UUID, data: ProjectUpdate) -> Project:
    """更新项目信息"""
    project = project_service.update(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


class SandboxTestResult(BaseModel):
    """沙箱连通性检查结果。"""
    ok: bool
    message: str


@router.post("/{project_id}/sandbox/test", response_model=SandboxTestResult)
async def test_sandbox(project_id: UUID) -> SandboxTestResult:
    """检查当前沙箱配置能否作为执行环境使用。"""
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    sandbox = project.sandbox
    backend = sandbox.get("backend") if isinstance(sandbox, dict) else sandbox.backend
    if backend == "local":
        return SandboxTestResult(ok=True, message="本地执行环境可用")
    return SandboxTestResult(ok=False, message=f"{backend} 尚未接入真实集群，配置已保存")


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID):
    """删除项目"""
    if not project_service.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
