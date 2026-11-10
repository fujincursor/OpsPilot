"""项目模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """项目状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProjectSkill(BaseModel):
    """项目启用的技能。"""
    key: str
    name: str
    description: str = ""
    enabled: bool = True
    usage_count: int = 0


class ProjectProfile(BaseModel):
    """提交需求前需要维护的项目资料。"""
    overview: str = ""
    architecture: str = ""
    directory_layout: str = ""
    key_modules: str = ""
    config_notes: str = ""
    runbook: str = ""


class ProjectMember(BaseModel):
    """项目成员。"""
    username: str
    role: str = "developer"


class SandboxSettings(BaseModel):
    """项目级沙箱配置。"""
    backend: str = "local"
    memory_mb: int = 512
    cpu: float = 1.0
    timeout_seconds: int = 300
    network_policy: str = "disabled"
    allowed_domains: List[str] = Field(default_factory=list)
    run_as_non_root: bool = True


def default_project_skills() -> List[ProjectSkill]:
    """内置技能。自定义 Webhook 技能不在本次范围。"""
    return [
        ProjectSkill(key="demand-analysis", name="需求分析", description="识别 Bug、新需求和咨询"),
        ProjectSkill(key="knowledge-search", name="知识检索", description="检索项目文档和代码索引"),
        ProjectSkill(key="code-generation", name="代码生成", description="按已通过的方案生成代码"),
        ProjectSkill(key="lint", name="语法检查", description="在沙箱中做静态检查"),
        ProjectSkill(key="test-execution", name="测试执行", description="生成并执行测试"),
    ]


class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, max_length=500, description="项目描述")
    repo_url: Optional[str] = Field(None, description="代码仓库地址")


class ProjectCreate(ProjectBase):
    """创建项目请求模型"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, max_length=500, description="项目描述")
    repo_url: Optional[str] = Field(None, description="代码仓库地址")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")
    skills: Optional[List[ProjectSkill]] = Field(None, description="项目技能")
    sandbox: Optional[SandboxSettings] = Field(None, description="沙箱配置")
    profile: Optional[ProjectProfile] = Field(None, description="项目资料")
    members: Optional[List[ProjectMember]] = Field(None, description="项目成员")
    prompt_template: Optional[str] = Field(None, description="项目 Prompt 模板")
    toolchain: Optional[str] = Field(None, description="工具链说明")


class Project(ProjectBase):
    """项目完整模型"""
    id: UUID = Field(default_factory=uuid4, description="项目 ID")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="项目状态")
    skills: List[ProjectSkill] = Field(default_factory=default_project_skills, description="项目技能")
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings, description="沙箱配置")
    profile: ProjectProfile = Field(default_factory=ProjectProfile, description="项目资料")
    members: List[ProjectMember] = Field(default_factory=list, description="项目成员")
    prompt_template: str = Field(default="", description="项目 Prompt 模板")
    toolchain: str = Field(default="", description="工具链说明")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """项目列表响应模型"""
    items: List[Project]
    total: int
    page: int = 1
    page_size: int = 20
