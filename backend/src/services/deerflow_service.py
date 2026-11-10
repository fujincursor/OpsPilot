"""DeerFlow 集成服务

通过 DeerFlowClient 嵌入式调用 DeerFlow Agent 系统。
提供需求分析、方案生成、代码生成、测试执行等完整运维工作流。
"""

import os
import sys
import json
import logging
from typing import Any, Dict, List, Optional, Generator
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 设置 DeerFlow 环境变量和路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DEERFLOW_PATH = PROJECT_ROOT / "deerflow" / "backend" / "packages" / "harness"

if DEERFLOW_PATH.exists():
    sys.path.insert(0, str(DEERFLOW_PATH))

# 设置 DeerFlow 配置路径
config_path = PROJECT_ROOT / "config.yaml"
if config_path.exists():
    os.environ.setdefault("DEER_FLOW_CONFIG_PATH", str(config_path))

skills_path = PROJECT_ROOT / "skills"
if skills_path.exists():
    os.environ.setdefault("DEER_FLOW_SKILLS_PATH", str(skills_path))

opspilot_home = PROJECT_ROOT / ".opspilot"
os.environ.setdefault("DEER_FLOW_HOME", str(opspilot_home))


@dataclass
class AgentResponse:
    """Agent 响应结构"""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[str] = None
    events: List[Dict[str, Any]] = field(default_factory=list)


class DeerFlowService:
    """DeerFlow 集成服务
    
    封装 DeerFlowClient，提供运维场景的 Agent 调用能力。
    """
    
    _instance = None
    _client = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._try_initialize()
            DeerFlowService._initialized = True
    
    def _try_initialize(self):
        """尝试初始化 DeerFlow Client"""
        try:
            from deerflow.client import DeerFlowClient
            
            self._client = DeerFlowClient()
            logger.info("DeerFlow Client 初始化成功")
            
        except ImportError as e:
            logger.warning(f"DeerFlow 未安装或导入失败: {e}")
            logger.info("将使用模拟模式运行")
            self._client = None
        except Exception as e:
            logger.error(f"DeerFlow Client 初始化失败: {e}")
            logger.info("将使用模拟模式运行")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """检查 DeerFlow 是否可用"""
        return self._client is not None
    
    def chat(
        self,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """发送消息给 Agent
        
        Args:
            message: 用户消息
            thread_id: 会话 ID（可选，用于多轮对话）
            context: 额外上下文
            
        Returns:
            AgentResponse: Agent 响应
        """
        if not self.is_available:
            return self._mock_chat(message, thread_id)
        
        try:
            response = self._client.chat(
                message,
                thread_id=thread_id,
                context=context or {}
            )
            
            return AgentResponse(
                success=True,
                message=response,
                thread_id=thread_id,
                data={"raw_response": response}
            )
            
        except Exception as e:
            logger.error(f"DeerFlow chat 失败: {e}")
            return AgentResponse(
                success=False,
                message=f"Agent 调用失败: {str(e)}",
                thread_id=thread_id
            )
    
    def stream(
        self,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """流式发送消息给 Agent
        
        Args:
            message: 用户消息
            thread_id: 会话 ID
            context: 额外上下文
            
        Yields:
            Dict: 流式事件
        """
        if not self.is_available:
            yield from self._mock_stream(message, thread_id)
            return
        
        try:
            for event in self._client.stream(message, thread_id=thread_id, context=context or {}):
                yield {
                    "type": event.type,
                    "data": event.data
                }
                
        except Exception as e:
            logger.error(f"DeerFlow stream 失败: {e}")
            yield {
                "type": "error",
                "data": {"error": str(e)}
            }
    
    def analyze_requirement(
        self,
        title: str,
        description: str,
        source: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """分析运维需求
        
        使用 requirement-analysis skill 分析需求。
        
        Args:
            title: 需求标题
            description: 需求描述
            source: 来源（github_issue, jira, alert 等）
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 分析结果
        """
        prompt = f"""请使用 requirement-analysis 技能分析以下运维需求：

## 需求标题
{title}

## 需求描述
{description}

## 来源
{source or '用户提交'}

请输出结构化的分析结果，包括：
1. 需求类型（bug/feature/enhancement/maintenance/security）
2. 优先级（P0-P3）
3. 影响评估
4. 复杂度评估
5. 相关知识库检索结果
6. 建议的下一步行动
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "requirement-analysis",
                "agent_name": "requirement_analyzer"
            }
        )
    
    def generate_bugfix_solution(
        self,
        requirement_id: str,
        analysis: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """生成 Bug 修复方案
        
        使用 bugfix-solution skill 生成修复方案。
        
        Args:
            requirement_id: 需求 ID
            analysis: 需求分析结果
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 修复方案
        """
        prompt = f"""请使用 bugfix-solution 技能为以下 Bug 生成修复方案：

## 需求 ID
{requirement_id}

## 需求分析
{json.dumps(analysis, ensure_ascii=False, indent=2)}

请输出完整的修复方案，包括：
1. 根因分析
2. 修复策略
3. 代码变更建议
4. 测试计划
5. 回滚方案
6. 风险评估
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "bugfix-solution",
                "agent_name": "bugfix_agent"
            }
        )
    
    def generate_feature_design(
        self,
        requirement_id: str,
        analysis: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """生成功能设计方案
        
        使用 feature-design skill 生成设计方案。
        
        Args:
            requirement_id: 需求 ID
            analysis: 需求分析结果
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 设计方案
        """
        prompt = f"""请使用 feature-design 技能为以下功能需求生成设计方案：

## 需求 ID
{requirement_id}

## 需求分析
{json.dumps(analysis, ensure_ascii=False, indent=2)}

请输出完整的设计方案，包括：
1. 功能概述和用户故事
2. 功能范围（in_scope / out_of_scope）
3. 技术架构设计
4. API 接口设计
5. 数据模型设计
6. 实施计划和里程碑
7. 测试策略
8. 风险评估
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "feature-design",
                "agent_name": "feature_agent"
            }
        )
    
    def generate_code(
        self,
        solution_id: str,
        solution: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """生成代码
        
        使用 code-generation skill 生成代码。
        
        Args:
            solution_id: 方案 ID
            solution: 解决方案
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 生成的代码
        """
        prompt = f"""请使用 code-generation 技能根据以下方案生成代码：

## 方案 ID
{solution_id}

## 解决方案
{json.dumps(solution, ensure_ascii=False, indent=2)}

请输出：
1. 代码文件列表和内容
2. 单元测试代码
3. API 文档
4. 变更说明
5. 代码质量检查结果
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "code-generation",
                "agent_name": "codegen_agent"
            }
        )
    
    def execute_tests(
        self,
        code_changes: List[Dict[str, Any]],
        test_type: str = "all",
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """执行测试
        
        使用 test-execution skill 执行测试。
        
        Args:
            code_changes: 代码变更列表
            test_type: 测试类型（unit/integration/all）
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 测试结果
        """
        prompt = f"""请使用 test-execution 技能执行以下测试：

## 测试类型
{test_type}

## 代码变更
{json.dumps(code_changes, ensure_ascii=False, indent=2)}

请执行测试并输出：
1. 测试结果汇总
2. 各测试套件详情
3. 失败用例分析
4. 覆盖率报告
5. 质量门禁检查结果
6. 建议的下一步行动
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "test-execution",
                "agent_name": "test_agent"
            }
        )
    
    def search_knowledge(
        self,
        query: str,
        thread_id: Optional[str] = None
    ) -> AgentResponse:
        """搜索知识库
        
        使用 knowledge-retrieval skill 搜索知识库。
        
        Args:
            query: 搜索查询
            thread_id: 会话 ID
            
        Returns:
            AgentResponse: 搜索结果
        """
        prompt = f"""请使用 knowledge-retrieval 技能搜索以下内容：

## 搜索查询
{query}

请返回：
1. 相关文档列表
2. 历史 Issue 案例
3. 最佳实践参考
4. 相关代码示例
"""
        
        return self.chat(
            prompt,
            thread_id=thread_id,
            context={
                "skill": "knowledge-retrieval"
            }
        )
    
    # ========== 模拟模式实现 ==========
    
    def _mock_chat(self, message: str, thread_id: Optional[str]) -> AgentResponse:
        """模拟 chat 响应"""
        logger.info(f"[模拟模式] 处理消息: {message[:100]}...")
        
        # 简单的关键词响应
        if "分析" in message or "需求" in message:
            response = self._mock_requirement_analysis(message)
        elif "修复" in message or "bug" in message.lower():
            response = self._mock_bugfix_solution(message)
        elif "设计" in message or "功能" in message:
            response = self._mock_feature_design(message)
        elif "代码" in message or "生成" in message:
            response = self._mock_code_generation(message)
        elif "测试" in message:
            response = self._mock_test_execution(message)
        else:
            response = f"[模拟响应] 已收到您的消息。当前处于模拟模式，请配置 DeerFlow 以获得完整功能。\n\n原始消息: {message[:200]}..."
        
        return AgentResponse(
            success=True,
            message=response,
            thread_id=thread_id,
            data={"mode": "mock"}
        )
    
    def _mock_stream(self, message: str, thread_id: Optional[str]):
        """模拟 stream 响应"""
        response = self._mock_chat(message, thread_id)
        
        # 模拟流式输出
        words = response.message.split()
        for i, word in enumerate(words):
            yield {
                "type": "messages-tuple",
                "data": {
                    "type": "ai",
                    "content": word + " ",
                    "id": f"mock-{i}"
                }
            }
        
        yield {
            "type": "end",
            "data": {}
        }
    
    def _mock_requirement_analysis(self, message: str) -> str:
        """模拟需求分析"""
        return """## 需求分析结果

**类型**: Bug（基于关键词检测）
**优先级**: P2 - 中
**置信度**: 0.75

### 影响评估
- 影响范围: 部分用户
- 业务影响: 一般业务功能

### 复杂度评估
- 技术复杂度: 中等
- 预估工作量: 2-3 天

### 建议行动
1. 分配给 BugFix Agent 处理
2. 需要人工确认优先级

---
*[模拟模式] 请配置 DeerFlow 获得真正的 AI 分析能力*
"""
    
    def _mock_bugfix_solution(self, message: str) -> str:
        """模拟 Bug 修复方案"""
        return """## Bug 修复方案

### 根因分析
基于描述，问题可能出在参数验证逻辑。

### 修复策略
采用常规修复策略，风险可控。

### 代码变更建议
```python
# 建议添加参数验证
def validate_input(data):
    if not data:
        raise ValueError("参数不能为空")
    return data
```

### 测试计划
1. 单元测试：验证参数校验逻辑
2. 集成测试：验证完整业务流程

### 回滚方案
如需回滚，执行 `git revert <commit-hash>`

---
*[模拟模式] 请配置 DeerFlow 获得真正的 AI 分析能力*
"""
    
    def _mock_feature_design(self, message: str) -> str:
        """模拟功能设计"""
        return """## 功能设计方案

### 功能概述
根据需求描述，设计新功能模块。

### 技术架构
- 前端: React + TypeScript
- 后端: FastAPI + Python
- 数据库: PostgreSQL

### API 设计
```
POST /api/v1/resource
GET /api/v1/resource/{id}
PUT /api/v1/resource/{id}
DELETE /api/v1/resource/{id}
```

### 实施计划
1. 阶段一：数据模型设计（1天）
2. 阶段二：API 实现（2天）
3. 阶段三：前端页面（2天）
4. 阶段四：测试和文档（1天）

---
*[模拟模式] 请配置 DeerFlow 获得真正的 AI 分析能力*
"""
    
    def _mock_code_generation(self, message: str) -> str:
        """模拟代码生成"""
        return """## 代码生成结果

### 生成的文件

**1. src/api/resource.py**
```python
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/resource")
async def list_resources():
    return {"items": []}

@router.post("/resource")
async def create_resource(data: dict):
    return {"id": "new-id", **data}
```

**2. tests/test_resource.py**
```python
import pytest

def test_list_resources():
    # Test implementation
    assert True

def test_create_resource():
    # Test implementation
    assert True
```

### 质量检查
- ✅ Lint 通过
- ✅ 类型检查通过
- ⚠️ 测试覆盖率: 60%（建议提升）

---
*[模拟模式] 请配置 DeerFlow 获得真正的 AI 分析能力*
"""
    
    def _mock_test_execution(self, message: str) -> str:
        """模拟测试执行"""
        return """## 测试执行结果

### 汇总
- 总计: 50
- 通过: 48
- 失败: 1
- 跳过: 1
- 耗时: 12.3s

### 覆盖率
- 行覆盖: 82.5%
- 分支覆盖: 75.0%

### 失败用例
```
FAILED tests/test_api.py::test_edge_case
  AssertionError: expected 200, got 400
```

### 建议
1. 修复 test_edge_case 中的断言问题
2. 补充边界条件测试

### 质量门禁
- ✅ 覆盖率 > 80%
- ❌ 无失败用例
- ✅ 执行时间 < 5min

**结论**: 需要修复失败用例后才能合并

---
*[模拟模式] 请配置 DeerFlow 获得真正的 AI 分析能力*
"""


# 单例实例
deerflow_service = DeerFlowService()
