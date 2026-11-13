"""项目管理 API"""

import asyncio
import shutil
import subprocess
import sys
from typing import List, Optional
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
from ...services.sandbox_service import sandbox_service
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


class SandboxTestCheck(BaseModel):
    """一项真实检查。"""
    name: str
    ok: bool
    detail: str


class SandboxTestResult(BaseModel):
    """沙箱连通性检查结果。"""
    ok: bool
    message: str
    checks: List[SandboxTestCheck] = []
    output: str = ""


def _probe(command: List[str]) -> tuple[bool, str]:
    if shutil.which(command[0]) is None:
        return False, f"未找到 {command[0]}"
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=8)
    except subprocess.TimeoutExpired:
        return False, "检查超时"
    text = (completed.stdout or completed.stderr or "").strip()
    first = text.splitlines()[0][:300] if text else "无输出"
    return completed.returncode == 0, first


@router.post("/{project_id}/sandbox/test", response_model=SandboxTestResult)
async def test_sandbox(project_id: UUID) -> SandboxTestResult:
    """检查当前沙箱配置能否作为执行环境使用。"""
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    sandbox = project.sandbox

    def field(name: str, default):
        if isinstance(sandbox, dict):
            return sandbox.get(name, default)
        return getattr(sandbox, name, default)

    backend = field("backend", "local")
    policy = field("network_policy", "disabled")
    memory = field("memory_mb", 512)
    cpu = field("cpu", 1)
    non_root = bool(field("run_as_non_root", True))

    if backend in {"local", "docker"}:
        python_ok, python_detail = await asyncio.to_thread(_probe, [sys.executable, "--version"])
        docker_ok, docker_detail = await asyncio.to_thread(_probe, ["docker", "version", "--format", "{{.Server.Version}}"])
        container_ok, container_detail = (False, "Docker 引擎不可用")
        if docker_ok:
            container_ok, container_detail = await asyncio.to_thread(
                sandbox_service.probe_execution,
                int(memory or 512),
                float(cpu or 1),
                str(policy or "disabled"),
                non_root,
            )
        if policy == "disabled":
            network_ok = container_ok
            network_detail = "已使用 --network none" if container_ok else "容器未启动，网络策略没有生效"
        elif policy == "allowlist":
            network_ok = False
            network_detail = "已保存域名白名单，容器仍使用默认网络，未按域名过滤"
        else:
            network_ok = container_ok
            network_detail = "已使用容器默认网络" if container_ok else "容器未启动"
        checks = [
            SandboxTestCheck(name="本机 Python", ok=python_ok, detail=python_detail),
            SandboxTestCheck(
                name="Docker 连接",
                ok=docker_ok and container_ok,
                detail=container_detail if docker_ok else "本机没有可用的 Docker，不会创建容器",
            ),
            SandboxTestCheck(
                name="资源限制",
                ok=container_ok,
                detail=f"已用 --memory {memory}m --cpus {cpu} 启动容器" if container_ok else "容器未启动，资源限制没有生效",
            ),
            SandboxTestCheck(
                name="非 root",
                ok=container_ok,
                detail="已使用 --user 65534:65534" if non_root else "配置为以 root 运行",
            ),
            SandboxTestCheck(name="网络策略", ok=network_ok, detail=network_detail),
            SandboxTestCheck(
                name="磁盘配额",
                ok=False,
                detail=f"已保存 {field('disk_gb', 10)}GB，Docker Desktop 未按该配额限制容器磁盘",
            ),
        ]
        if not docker_ok:
            message = "已选择 Docker AIO，本机没有可用的 Docker。"
        elif container_ok:
            message = f"容器执行已启用。引擎 {docker_detail}。"
        else:
            message = "Docker 引擎可用，但沙箱容器没有启动。"
        output = container_detail if container_ok else docker_detail
        return SandboxTestResult(ok=container_ok, message=message, checks=checks, output=output)

    if backend == "kubernetes":
        return SandboxTestResult(
            ok=False,
            message="Kubernetes 尚未接入真实集群，配置已保存。",
            checks=[SandboxTestCheck(name="集群连接", ok=False, detail="没有可用的集群客户端")],
        )

    if backend == "e2b":
        key = sandbox.get("e2b_api_key") if isinstance(sandbox, dict) else sandbox.e2b_api_key
        detail = "尚未向 E2B 发起验证" if key else "未填写 API Key"
        return SandboxTestResult(
            ok=False,
            message="E2B Cloud 尚未接入。",
            checks=[SandboxTestCheck(name="API Key", ok=False, detail=detail)],
        )

    return SandboxTestResult(ok=False, message=f"{backend} 不是已支持的执行环境")


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID):
    """删除项目"""
    if not project_service.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
