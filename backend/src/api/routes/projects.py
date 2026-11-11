"""项目管理 API"""

import asyncio
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from ...models.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectStatus
)
from ...services.project_service import project_service
from ...services.workspace_service import WorkspaceError, workspace_service

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


class GitImportRequest(BaseModel):
    """从 Git 仓库导入源代码。"""
    repo_url: str
    branch: str = ""


@router.post("/{project_id}/code/git", response_model=Project)
async def import_project_git(project_id: UUID, data: GitImportRequest) -> Project:
    """把仓库克隆到该项目的工作目录，并作为后续方案和代码生成的唯一代码来源。"""
    if not project_service.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        return await asyncio.to_thread(
            workspace_service.import_git,
            project_id,
            data.repo_url,
            data.branch,
        )
    except WorkspaceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/code/upload", response_model=Project)
async def import_project_zip(
    project_id: UUID,
    file: UploadFile = File(...),
) -> Project:
    """把上传的 zip 解压到该项目的工作目录。"""
    if not project_service.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    payload = await file.read()
    try:
        return await asyncio.to_thread(
            workspace_service.import_zip,
            project_id,
            payload,
            file.filename or "source.zip",
        )
    except WorkspaceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
