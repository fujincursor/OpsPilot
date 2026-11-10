"""Agent 配置模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Agent 类型"""
    LEAD = "lead"
    BUG_FIX = "bugfix"
    FEATURE_DESIGN = "feature"
    CODE_GENERATION = "codegen"
    TEST_EXECUTION = "test"


class AgentConfigBase(BaseModel):
    """Agent 配置基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent 名称")
    agent_type: AgentType = Field(..., description="Agent 类型")
    description: Optional[str] = Field(None, max_length=500, description="Agent 描述")
    model_name: str = Field(default="gpt-4", description="使用的模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="模型温度参数")
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="最大 token 数")
    skills: List[str] = Field(default_factory=list, description="Agent 技能列表")
    enabled: bool = Field(default=True, description="是否启用")


class AgentConfigCreate(BaseModel):
    """创建 Agent 配置请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent 名称")
    agent_type: AgentType = Field(..., description="Agent 类型")
    description: Optional[str] = Field(None, max_length=500, description="Agent 描述")
    model_name: Optional[str] = Field(default="gpt-4", description="使用的模型名称")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="模型温度参数")
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=128000, description="最大 token 数")
    skills: Optional[List[str]] = Field(default_factory=list, description="Agent 技能列表")
    enabled: Optional[bool] = Field(default=True, description="是否启用")


class AgentConfigUpdate(BaseModel):
    """更新 Agent 配置请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Agent 名称")
    description: Optional[str] = Field(None, max_length=500, description="Agent 描述")
    model_name: Optional[str] = Field(None, description="使用的模型名称")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="模型温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, le=128000, description="最大 token 数")
    skills: Optional[List[str]] = Field(None, description="Agent 技能列表")
    enabled: Optional[bool] = Field(None, description="是否启用")


class AgentConfig(AgentConfigBase):
    """Agent 配置完整模型"""
    id: UUID = Field(default_factory=uuid4, description="Agent 配置 ID")
    project_id: UUID = Field(..., description="所属项目 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        from_attributes = True


class AgentConfigResponse(BaseModel):
    """Agent 配置列表响应模型"""
    items: List[AgentConfig]
    total: int
