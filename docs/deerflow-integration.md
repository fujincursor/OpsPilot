# DeerFlow 集成指南

本文档说明如何在 OpsPilot 中集成和使用 DeerFlow 框架。

## 概述

OpsPilot 运维领航基于 DeerFlow 2.0 框架构建，利用其 Lead Agent + Sub-Agents 架构实现智能运维工作流。

### 架构对应关系

| OpsPilot 组件 | DeerFlow 组件 |
|--------------|---------------|
| Lead Agent | DeerFlow Lead Agent |
| 需求分析 Agent | Sub-Agent (requirement_analyzer) |
| Bug 修复 Agent | Sub-Agent (bugfix_agent) |
| 功能设计 Agent | Sub-Agent (feature_agent) |
| 代码生成 Agent | Sub-Agent (codegen_agent) |
| 测试 Agent | Sub-Agent (test_agent) |
| Skills | DeerFlow Skills (SKILL.md) |
| 知识库 | DeerFlow Memory + Knowledge Base |
| Sandbox | DeerFlow Sandbox (Docker) |

## 快速开始

### 1. 环境准备

```bash
# 确保 DeerFlow 已克隆
cd /path/to/OpsPilot
ls deerflow/  # 应该看到 DeerFlow 代码

# 安装依赖
cd backend
pip install -r requirements.txt

# 安装 DeerFlow（可选，用于完整功能）
pip install -e ../deerflow/backend/packages/harness
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

必需的环境变量：

```env
# LLM API Keys（至少配置一个）
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-xxx

# 可选：搜索功能
TAVILY_API_KEY=tvly-xxx

# 可选：知识库
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=ragflow-xxx
```

### 3. 配置 config.yaml

编辑项目根目录的 `config.yaml`，配置模型和 Skills：

```yaml
# 模型配置
models:
  - name: gpt-4o
    display_name: GPT-4o
    use: langchain_openai:ChatOpenAI
    model: gpt-4o
    api_key: $OPENAI_API_KEY

# Skills 配置
skills:
  paths:
    - skills/opspilot
  enabled:
    - requirement-analysis
    - bugfix-solution
    - feature-design
    - code-generation
    - test-execution
    - knowledge-retrieval
```

### 4. 启动服务

```bash
# 启动后端
cd backend
uvicorn src.main:app --reload --port 8000

# 启动前端
cd frontend
npm run dev
```

## Skills 说明

OpsPilot 定义了 6 个专属 Skills：

### 1. requirement-analysis（需求分析）

位置：`skills/opspilot/requirement-analysis/SKILL.md`

功能：
- 分析运维需求（Bug、Feature、Enhancement 等）
- 优先级评估（P0-P3）
- 影响范围评估
- 知识库关联

### 2. bugfix-solution（Bug 修复方案）

位置：`skills/opspilot/bugfix-solution/SKILL.md`

功能：
- 根因分析（5 Whys 方法）
- 修复策略选择
- 代码变更建议
- 测试计划
- 回滚方案

### 3. feature-design（功能设计）

位置：`skills/opspilot/feature-design/SKILL.md`

功能：
- 用户故事分析
- 技术架构设计
- API 接口设计
- 数据模型设计
- 实施计划

### 4. code-generation（代码生成）

位置：`skills/opspilot/code-generation/SKILL.md`

功能：
- 代码实现
- 单元测试生成
- 文档生成
- 代码质量检查

### 5. test-execution（测试执行）

位置：`skills/opspilot/test-execution/SKILL.md`

功能：
- 单元测试执行
- 集成测试执行
- 覆盖率报告
- 质量门禁检查

### 6. knowledge-retrieval（知识检索）

位置：`skills/opspilot/knowledge-retrieval/SKILL.md`

功能：
- 文档搜索
- 历史案例查询
- 最佳实践推荐
- 代码示例检索

## API 使用

### DeerFlow Agent API

所有 DeerFlow Agent 相关的 API 都在 `/api/v1/deerflow/` 路径下：

```
GET  /api/v1/deerflow/status          # 获取 Agent 状态
POST /api/v1/deerflow/chat            # 与 Agent 对话
POST /api/v1/deerflow/chat/stream     # 流式对话
POST /api/v1/deerflow/analyze-requirement  # 分析需求
POST /api/v1/deerflow/generate-bugfix      # 生成 Bug 修复方案
POST /api/v1/deerflow/generate-feature     # 生成功能设计
POST /api/v1/deerflow/generate-code        # 生成代码
POST /api/v1/deerflow/execute-tests        # 执行测试
POST /api/v1/deerflow/search-knowledge     # 搜索知识库
POST /api/v1/deerflow/workflow/start       # 启动工作流
```

### 示例：分析需求

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/deerflow/analyze-requirement",
    json={
        "title": "登录页面报 500 错误",
        "description": "用户反馈在登录时偶发 500 错误，日志显示数据库连接超时",
        "source": "github_issue"
    }
)

print(response.json())
```

### 示例：流式对话

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/deerflow/chat/stream",
    json={"message": "请分析这个 Bug"},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode())
```

## 工作流程

### 完整运维工作流

```
1. 需求提交
   ↓
2. Lead Agent 接收并调用 requirement-analysis Skill
   ↓
3. 需求分类和优先级评估
   ↓
4. 根据类型分发给对应 Sub-Agent
   ├── Bug → bugfix_agent
   └── Feature → feature_agent
   ↓
5. 方案生成
   ↓
6. HITL 人工审核
   ↓
7. 审核通过 → codegen_agent 生成代码
   ↓
8. test_agent 执行测试
   ↓
9. 测试通过 → 提交 PR
   ↓
10. 更新知识库
```

## 模拟模式

当 DeerFlow 未完全配置时，系统会自动进入模拟模式：

- API 正常响应
- 返回模拟的分析结果
- 提示用户配置 DeerFlow

检查当前模式：

```bash
curl http://localhost:8000/api/v1/deerflow/status
```

响应：
```json
{
  "available": false,
  "mode": "mock",
  "version": null
}
```

## 故障排除

### DeerFlow 导入失败

```
ImportError: No module named 'deerflow'
```

解决：
```bash
pip install -e ./deerflow/backend/packages/harness
```

### 模型调用失败

检查：
1. API Key 是否正确配置
2. config.yaml 中模型配置是否正确
3. 网络是否可访问模型 API

### Sandbox 执行失败

检查：
1. Docker 是否安装并运行
2. config.yaml 中 sandbox 配置是否正确

## 参考链接

- [DeerFlow 官方文档](https://github.com/bytedance/deer-flow)
- [DeerFlow 中文文档](./deerflow/README_zh.md)
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
