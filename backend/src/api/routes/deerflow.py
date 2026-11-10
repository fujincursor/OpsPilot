"""DeerFlow Agent API 路由

提供 DeerFlow Agent 系统的 HTTP API 接口。
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import json

from ...services.deerflow_service import deerflow_service


router = APIRouter(prefix="/deerflow", tags=["DeerFlow Agent"])


# ========== 请求模型 ==========

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    thread_id: Optional[str] = Field(None, description="会话 ID")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")


class RequirementAnalysisRequest(BaseModel):
    """需求分析请求"""
    title: str = Field(..., description="需求标题")
    description: str = Field(..., description="需求描述")
    source: Optional[str] = Field(None, description="来源类型")
    thread_id: Optional[str] = Field(None, description="会话 ID")


class SolutionRequest(BaseModel):
    """方案生成请求"""
    requirement_id: str = Field(..., description="需求 ID")
    analysis: Dict[str, Any] = Field(..., description="需求分析结果")
    thread_id: Optional[str] = Field(None, description="会话 ID")


class CodeGenerationRequest(BaseModel):
    """代码生成请求"""
    solution_id: str = Field(..., description="方案 ID")
    solution: Dict[str, Any] = Field(..., description="解决方案")
    thread_id: Optional[str] = Field(None, description="会话 ID")


class TestExecutionRequest(BaseModel):
    """测试执行请求"""
    code_changes: List[Dict[str, Any]] = Field(..., description="代码变更列表")
    test_type: str = Field("all", description="测试类型")
    thread_id: Optional[str] = Field(None, description="会话 ID")


class KnowledgeSearchRequest(BaseModel):
    """知识搜索请求"""
    query: str = Field(..., description="搜索查询")
    thread_id: Optional[str] = Field(None, description="会话 ID")


# ========== 响应模型 ==========

class AgentStatus(BaseModel):
    """Agent 状态"""
    available: bool
    mode: str
    version: Optional[str] = None


class AgentResponseModel(BaseModel):
    """Agent 响应"""
    success: bool
    message: str
    data: Dict[str, Any] = {}
    thread_id: Optional[str] = None


# ========== API 端点 ==========

@router.get("/status", response_model=AgentStatus)
async def get_agent_status():
    """获取 DeerFlow Agent 状态
    
    返回 Agent 是否可用以及运行模式。
    """
    return AgentStatus(
        available=deerflow_service.is_available,
        mode="deerflow" if deerflow_service.is_available else "mock",
        version="2.0" if deerflow_service.is_available else None
    )


@router.post("/chat", response_model=AgentResponseModel)
async def chat(request: ChatRequest):
    """与 Agent 对话
    
    发送消息给 Agent，获取响应。
    """
    response = deerflow_service.chat(
        message=request.message,
        thread_id=request.thread_id,
        context=request.context
    )
    
    return AgentResponseModel(
        success=response.success,
        message=response.message,
        data=response.data,
        thread_id=response.thread_id
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """与 Agent 流式对话
    
    发送消息给 Agent，获取流式响应。
    """
    async def generate():
        for event in deerflow_service.stream(
            message=request.message,
            thread_id=request.thread_id,
            context=request.context
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/analyze-requirement", response_model=AgentResponseModel)
async def analyze_requirement(request: RequirementAnalysisRequest):
    """分析需求
    
    使用 Lead Agent 分析需求，返回类型、优先级等信息。
    """
    response = deerflow_service.analyze_requirement(
        title=request.title,
        description=request.description,
        source=request.source,
        thread_id=request.thread_id
    )
    
    return AgentResponseModel(
        success=response.success,
        message=response.message,
        data=response.data,
        thread_id=response.thread_id
    )


@router.post("/generate-bugfix", response_model=AgentResponseModel)
async def generate_bugfix_solution(request: SolutionRequest):
    """生成 Bug 修复方案
    
    使用 BugFix Agent 生成修复方案。
    """
    response = deerflow_service.generate_bugfix_solution(
        requirement_id=request.requirement_id,
        analysis=request.analysis,
        thread_id=request.thread_id
    )
    
    return AgentResponseModel(
        success=response.success,
        message=response.message,
        data=response.data,
        thread_id=response.thread_id
    )


@router.post("/generate-feature", response_model=AgentResponseModel)
async def generate_feature_design(request: SolutionRequest):
    """生成功能设计方案
    
    使用 Feature Agent 生成设计方案。
    """
    response = deerflow_service.generate_feature_design(
        requirement_id=request.requirement_id,
        analysis=request.analysis,
        thread_id=request.thread_id
    )
    
    return AgentResponseModel(
        success=response.success,
        message=response.message,
        data=response.data,
        thread_id=response.thread_id
    )


@router.post("/generate-code", response_model=AgentResponseModel)
async def generate_code(request: CodeGenerationRequest):
    """生成代码
    
    使用 CodeGen Agent 根据方案生成代码。
    """
    response = deerflow_service.generate_code(
        solution_id=request.solution_id,
        solution=request.solution,
        thread_id=request.thread_id
    )
    
    return AgentResponseModel(
        success=response.success,
        message=response.message,
        data=response.data,
        thread_id=response.thread_id
    )


@router.post("/execute-tests", response_model=AgentResponseModel)
async def execute_tests(request: TestExecutionRequest):
    """执行测试
    
    使用 Test Agent 执行测试并返回结果。
    """
    response = deerflow_service.execute_tests(
        code_changes=request.code_changes,
        test_type=request.test_type,
        thread_id=request.thread_id
    )
    
    return AgentResponseModel(
        success=response.success,
        message=response.message,
        data=response.data,
        thread_id=response.thread_id
    )


@router.post("/search-knowledge", response_model=AgentResponseModel)
async def search_knowledge(request: KnowledgeSearchRequest):
    """搜索知识库
    
    搜索运维知识库，返回相关文档和案例。
    """
    response = deerflow_service.search_knowledge(
        query=request.query,
        thread_id=request.thread_id
    )
    
    return AgentResponseModel(
        success=response.success,
        message=response.message,
        data=response.data,
        thread_id=response.thread_id
    )


# ========== 工作流 API ==========

class WorkflowRequest(BaseModel):
    """完整工作流请求"""
    title: str = Field(..., description="需求标题")
    description: str = Field(..., description="需求描述")
    source: Optional[str] = Field(None, description="来源")
    auto_execute: bool = Field(False, description="是否自动执行全流程")


@router.post("/workflow/start", response_model=AgentResponseModel)
async def start_workflow(request: WorkflowRequest):
    """启动运维工作流
    
    从需求分析开始，根据分析结果自动或手动推进后续流程。
    
    工作流步骤：
    1. 需求分析 -> 2. 方案生成 -> 3. 人工审核 -> 4. 代码生成 -> 5. 测试执行 -> 6. 完成
    """
    # 第一步：需求分析
    analysis_response = deerflow_service.analyze_requirement(
        title=request.title,
        description=request.description,
        source=request.source
    )
    
    if not analysis_response.success:
        return AgentResponseModel(
            success=False,
            message="需求分析失败",
            data={"step": "analysis", "error": analysis_response.message}
        )
    
    workflow_data = {
        "step": "analysis_complete",
        "analysis": analysis_response.message,
        "next_step": "solution_generation",
        "requires_approval": True,
        "thread_id": analysis_response.thread_id
    }
    
    # 如果需要自动执行，继续下一步
    if request.auto_execute:
        # 根据需求类型选择方案生成方式
        # 这里简化处理，实际应该解析分析结果
        workflow_data["auto_execute"] = True
        workflow_data["message"] = "工作流已启动，等待人工审核后继续..."
    
    return AgentResponseModel(
        success=True,
        message="需求分析完成，请审核后继续",
        data=workflow_data,
        thread_id=analysis_response.thread_id
    )
