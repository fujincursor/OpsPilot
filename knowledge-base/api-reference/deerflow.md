# DeerFlow Agent API

## 概述

DeerFlow Agent API 提供与 AI Agent 交互的接口，支持对话、分析、生成等功能。

**基础路径**: `/api/v1/deerflow`

## 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/deerflow/status` | 获取 DeerFlow 状态 |
| POST | `/deerflow/chat` | 发送消息 |
| POST | `/deerflow/chat/stream` | 流式对话 |
| POST | `/deerflow/analyze-requirement` | 需求分析 |
| POST | `/deerflow/generate-bugfix` | 生成 Bug 修复方案 |
| POST | `/deerflow/generate-feature` | 生成功能设计 |
| POST | `/deerflow/generate-code` | 生成代码 |
| POST | `/deerflow/execute-tests` | 执行测试 |
| POST | `/deerflow/search-knowledge` | 知识搜索 |
| POST | `/deerflow/workflow/start` | 启动工作流 |

---

## GET /deerflow/status

获取 DeerFlow 服务状态。

### 请求示例

```http
GET /api/v1/deerflow/status
Authorization: Bearer <token>
```

### 响应示例

```json
{
  "data": {
    "status": "operational",
    "version": "2.0.0",
    "mode": "production",
    "agents": {
      "lead_agent": "active",
      "sub_agents": {
        "researcher": "active",
        "coder": "active",
        "reporter": "active"
      }
    },
    "models": {
      "primary": "gpt-4o",
      "fallback": "deepseek-chat"
    }
  }
}
```

---

## POST /deerflow/chat

与 Agent 进行对话。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `message` | string | 是 | 用户消息 |
| `thread_id` | string | 否 | 会话 ID |
| `context` | object | 否 | 上下文信息 |

### 请求示例

```http
POST /api/v1/deerflow/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "分析这个 Bug：用户登录时返回 500 错误",
  "thread_id": "thread_abc123",
  "context": {
    "project_id": "proj_123",
    "requirement_id": "req_456"
  }
}
```

### 响应示例

```json
{
  "data": {
    "response": "根据分析，这个 Bug 的可能原因是...",
    "thread_id": "thread_abc123",
    "agent": "lead_agent",
    "thinking_process": [
      "分析错误日志...",
      "检查认证模块...",
      "定位到数据库连接问题..."
    ],
    "suggestions": [
      {
        "action": "查看详细分析",
        "endpoint": "/analyze-requirement"
      }
    ],
    "metadata": {
      "tokens_used": 1250,
      "model": "gpt-4o",
      "duration_ms": 3500
    }
  }
}
```

---

## POST /deerflow/chat/stream

流式对话，实时返回 Agent 响应。

### 请求体

同 `/deerflow/chat`

### 请求示例

```http
POST /api/v1/deerflow/chat/stream
Authorization: Bearer <token>
Content-Type: application/json
Accept: text/event-stream

{
  "message": "帮我设计一个用户导出功能"
}
```

### 响应格式 (SSE)

```
data: {"type": "thinking", "content": "分析需求..."}

data: {"type": "content", "content": "好的，我来帮您设计"}

data: {"type": "content", "content": "用户导出功能..."}

data: {"type": "done", "thread_id": "thread_xyz"}
```

---

## POST /deerflow/analyze-requirement

分析需求。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 需求标题 |
| `description` | string | 是 | 需求描述 |
| `source` | string | 否 | 需求来源 |
| `thread_id` | string | 否 | 会话 ID |

### 请求示例

```http
POST /api/v1/deerflow/analyze-requirement
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "用户登录返回 500 错误",
  "description": "用户在登录时随机出现 500 错误，约 5% 的登录请求受影响",
  "source": "jira",
  "thread_id": "thread_abc123"
}
```

### 响应示例

```json
{
  "data": {
    "requirement_id": "req_789",
    "analysis": {
      "type": "bug",
      "severity": "high",
      "summary": "用户登录时数据库连接池耗尽导致 500 错误",
      "root_cause": {
        "description": "数据库连接未正确释放",
        "evidence": [
          "错误日志显示连接超时",
          "5% 的失败率与高峰期吻合"
        ]
      },
      "impact": {
        "affected_users": "约 5% 的用户",
        "business_impact": "影响用户体验和转化率"
      },
      "affected_modules": [
        "auth-service",
        "database-pool"
      ],
      "suggested_priority": "P1",
      "estimated_effort": "medium"
    },
    "next_steps": [
      {
        "action": "生成修复方案",
        "endpoint": "/generate-bugfix"
      }
    ]
  }
}
```

---

## POST /deerflow/generate-bugfix

生成 Bug 修复方案。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `requirement_id` | string | 是 | 需求 ID |
| `analysis` | object | 是 | 分析结果 |
| `thread_id` | string | 否 | 会话 ID |

### 请求示例

```http
POST /api/v1/deerflow/generate-bugfix
Authorization: Bearer <token>
Content-Type: application/json

{
  "requirement_id": "req_789",
  "analysis": {
    "type": "bug",
    "root_cause": {
      "description": "数据库连接未正确释放"
    }
  }
}
```

### 响应示例

```json
{
  "data": {
    "solution_id": "sol_abc",
    "solution": {
      "title": "修复数据库连接池泄漏",
      "approach": "使用 context manager 确保连接正确释放",
      "code_changes": [
        {
          "file": "src/db/connection.py",
          "description": "改用 async with 管理连接",
          "before": "conn = await pool.acquire()",
          "after": "async with pool.acquire() as conn:"
        }
      ],
      "test_plan": {
        "unit_tests": [
          "test_connection_release",
          "test_connection_pool_exhaustion"
        ],
        "integration_tests": [
          "test_concurrent_logins"
        ]
      },
      "risk_assessment": {
        "level": "low",
        "factors": ["改动范围小", "有测试覆盖"]
      },
      "rollback_plan": "回滚到上一版本的 connection.py"
    },
    "requires_review": true
  }
}
```

---

## POST /deerflow/generate-feature

生成功能设计方案。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `requirement_id` | string | 是 | 需求 ID |
| `analysis` | object | 是 | 分析结果 |
| `thread_id` | string | 否 | 会话 ID |

### 请求示例

```http
POST /api/v1/deerflow/generate-feature
Authorization: Bearer <token>
Content-Type: application/json

{
  "requirement_id": "req_feature_001",
  "analysis": {
    "type": "feature",
    "summary": "批量用户导出功能"
  }
}
```

### 响应示例

```json
{
  "data": {
    "solution_id": "sol_feature_001",
    "design": {
      "title": "批量用户导出功能设计",
      "overview": "支持管理员批量导出用户数据为 CSV/Excel 格式",
      "components": [
        {
          "name": "ExportService",
          "type": "service",
          "responsibilities": ["数据查询", "格式转换", "文件生成"]
        },
        {
          "name": "ExportAPI",
          "type": "api",
          "endpoints": [
            {"method": "POST", "path": "/exports", "description": "创建导出任务"},
            {"method": "GET", "path": "/exports/{id}", "description": "获取导出状态"}
          ]
        }
      ],
      "data_model": {
        "ExportTask": {
          "fields": ["id", "status", "format", "created_at", "file_url"]
        }
      },
      "api_design": [
        {
          "method": "POST",
          "path": "/api/v1/exports",
          "request": {"fields": ["id", "name"], "format": "csv"},
          "response": {"task_id": "export_123"}
        }
      ]
    },
    "requires_review": true
  }
}
```

---

## POST /deerflow/generate-code

根据方案生成代码。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `solution_id` | string | 是 | 方案 ID |
| `solution` | object | 是 | 方案内容 |
| `thread_id` | string | 否 | 会话 ID |

### 响应示例

```json
{
  "data": {
    "generation_id": "gen_123",
    "files": [
      {
        "path": "src/services/export_service.py",
        "action": "create",
        "content": "...",
        "language": "python"
      }
    ],
    "tests": [
      {
        "path": "tests/test_export_service.py",
        "content": "..."
      }
    ],
    "quality_report": {
      "lint_passed": true,
      "type_check_passed": true,
      "overall_score": 0.92
    }
  }
}
```

---

## POST /deerflow/execute-tests

执行测试。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `code_changes` | array | 是 | 代码变更 |
| `test_type` | string | 否 | 测试类型 |
| `thread_id` | string | 否 | 会话 ID |

### 响应示例

```json
{
  "data": {
    "test_run_id": "run_456",
    "status": "completed",
    "summary": {
      "total": 15,
      "passed": 14,
      "failed": 1,
      "pass_rate": 0.93
    },
    "coverage": {
      "line_coverage": 85.5
    },
    "failures": [
      {
        "test_name": "test_timeout",
        "error": "TimeoutError"
      }
    ]
  }
}
```

---

## POST /deerflow/search-knowledge

搜索知识库。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 搜索查询 |
| `thread_id` | string | 否 | 会话 ID |

### 响应示例

```json
{
  "data": {
    "results": [
      {
        "id": "doc_123",
        "title": "用户认证模块设计文档",
        "content": "...",
        "relevance_score": 0.95
      }
    ],
    "total": 5
  }
}
```

---

## POST /deerflow/workflow/start

启动完整工作流。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `requirement_id` | string | 是 | 需求 ID |
| `workflow_type` | string | 是 | 工作流类型 |

### 请求示例

```http
POST /api/v1/deerflow/workflow/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "requirement_id": "req_789",
  "workflow_type": "bugfix"
}
```

### 响应示例

```json
{
  "data": {
    "workflow_id": "wf_001",
    "status": "running",
    "current_stage": "analysis",
    "stages": [
      {"name": "analysis", "status": "completed"},
      {"name": "solution_generation", "status": "running"},
      {"name": "review", "status": "pending"},
      {"name": "code_generation", "status": "pending"},
      {"name": "testing", "status": "pending"}
    ]
  }
}
```

---

*文档版本: 1.0*
