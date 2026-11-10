"""Agent 配置管理 API"""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...models.agent import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse
)
from ...services.agent_service import agent_service
from ...services.project_service import project_service

router = APIRouter()


@router.get(
    "/projects/{project_id}/agents",
    response_model=AgentConfigResponse,
    tags=["agents"]
)
async def list_project_agents(project_id: UUID) -> AgentConfigResponse:
    """
    获取项目的所有 Agent 配置

    - **project_id**: 项目 ID
    """
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agents = agent_service.get_agents_by_project(project_id)
    return AgentConfigResponse(items=agents, total=len(agents))


@router.post(
    "/projects/{project_id}/agents",
    response_model=AgentConfig,
    status_code=201,
    tags=["agents"]
)
async def create_agent(project_id: UUID, data: AgentConfigCreate) -> AgentConfig:
    """
    为项目创建新的 Agent 配置

    - **project_id**: 项目 ID
    - **name**: Agent 名称 (必填, 1-100字符)
    - **agent_type**: Agent 类型 (lead/bugfix/feature/codegen/test)
    - **description**: Agent 描述 (可选)
    - **model_name**: 使用的模型名称 (默认: gpt-4)
    - **temperature**: 模型温度参数 (0.0-2.0, 默认: 0.7)
    - **max_tokens**: 最大 token 数 (默认: 4096)
    - **skills**: 技能列表
    - **enabled**: 是否启用 (默认: true)
    """
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return agent_service.create_agent(project_id, data)


@router.get(
    "/agents/{agent_id}",
    response_model=AgentConfig,
    tags=["agents"]
)
async def get_agent(agent_id: UUID) -> AgentConfig:
    """
    获取单个 Agent 配置详情

    - **agent_id**: Agent 配置 ID
    """
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put(
    "/agents/{agent_id}",
    response_model=AgentConfig,
    tags=["agents"]
)
async def update_agent(agent_id: UUID, data: AgentConfigUpdate) -> AgentConfig:
    """
    更新 Agent 配置

    - **agent_id**: Agent 配置 ID
    - 可更新字段: name, description, model_name, temperature, max_tokens, skills, enabled
    """
    agent = agent_service.update_agent(agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete(
    "/agents/{agent_id}",
    status_code=204,
    tags=["agents"]
)
async def delete_agent(agent_id: UUID):
    """
    删除 Agent 配置

    - **agent_id**: Agent 配置 ID
    """
    if not agent_service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")


@router.post(
    "/projects/{project_id}/agents/initialize",
    response_model=AgentConfigResponse,
    tags=["agents"]
)
async def initialize_project_agents(project_id: UUID) -> AgentConfigResponse:
    """
    为项目初始化默认 Agent 配置

    如果项目已有 Agent 配置，此操作将添加更多默认配置。
    建议仅在新项目上调用此接口。

    - **project_id**: 项目 ID
    """
    project = project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agents = agent_service.initialize_default_agents(project_id)
    return AgentConfigResponse(items=agents, total=len(agents))
