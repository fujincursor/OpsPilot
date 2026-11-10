# OpsPilot API 参考概述

## 1. API 简介

OpsPilot 提供 RESTful API 接口，支持所有核心功能的程序化访问。

### 1.1 基础信息

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://localhost:8000/api/v1` |
| **协议** | HTTP/HTTPS |
| **格式** | JSON |
| **认证** | Bearer Token |
| **版本** | v1 |

### 1.2 API 模块

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| **项目管理** | `/projects` | 项目和 Agent 管理 |
| **知识库** | `/knowledge` | 知识库管理 |
| **需求** | `/requirements` | 需求管理 |
| **方案** | `/solutions` | 方案管理 |
| **审核** | `/reviews` | 审核工作台 |
| **代码生成** | `/codegen` | 代码生成 |
| **测试** | `/tests` | 测试执行 |
| **DeerFlow** | `/deerflow` | AI Agent 交互 |

## 2. 认证

### 2.1 获取 Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

响应：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2.2 使用 Token

在请求头中添加：
```
Authorization: Bearer <access_token>
```

### 2.3 刷新 Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer <access_token>
```

## 3. 请求格式

### 3.1 请求头

| Header | 必需 | 说明 |
|--------|------|------|
| `Authorization` | 是 | Bearer Token |
| `Content-Type` | 是 | `application/json` |
| `Accept` | 否 | `application/json` |
| `X-Request-ID` | 否 | 请求追踪 ID |

### 3.2 请求体

所有 POST/PUT/PATCH 请求使用 JSON 格式：

```json
{
  "field1": "value1",
  "field2": 123,
  "nested": {
    "key": "value"
  }
}
```

## 4. 响应格式

### 4.1 成功响应

```json
{
  "data": {
    // 响应数据
  },
  "meta": {
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### 4.2 分页响应

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### 4.3 错误响应

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "meta": {
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

## 5. HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| `200 OK` | 请求成功 |
| `201 Created` | 创建成功 |
| `204 No Content` | 删除成功 |
| `400 Bad Request` | 请求参数错误 |
| `401 Unauthorized` | 未认证 |
| `403 Forbidden` | 无权限 |
| `404 Not Found` | 资源不存在 |
| `422 Unprocessable Entity` | 验证失败 |
| `429 Too Many Requests` | 请求过多 |
| `500 Internal Server Error` | 服务器错误 |

## 6. 错误码

| 错误码 | 说明 |
|--------|------|
| `AUTH_INVALID_TOKEN` | Token 无效 |
| `AUTH_TOKEN_EXPIRED` | Token 过期 |
| `VALIDATION_ERROR` | 参数验证失败 |
| `RESOURCE_NOT_FOUND` | 资源不存在 |
| `PERMISSION_DENIED` | 权限不足 |
| `RATE_LIMIT_EXCEEDED` | 超出速率限制 |
| `INTERNAL_ERROR` | 内部错误 |

## 7. 速率限制

| 端点类型 | 限制 |
|----------|------|
| 普通 API | 100 请求/分钟 |
| AI 交互 | 20 请求/分钟 |
| 认证 | 10 请求/分钟 |

超出限制时返回：
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

## 8. 通用查询参数

### 8.1 分页

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码 |
| `size` | int | 20 | 每页数量 |

### 8.2 排序

| 参数 | 类型 | 说明 |
|------|------|------|
| `sort_by` | string | 排序字段 |
| `order` | string | `asc` 或 `desc` |

### 8.3 过滤

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 状态过滤 |
| `created_after` | datetime | 创建时间起始 |
| `created_before` | datetime | 创建时间结束 |

## 9. WebSocket API

### 9.1 连接

```
ws://localhost:8000/ws?token=<access_token>
```

### 9.2 消息格式

```json
{
  "type": "message_type",
  "data": {...},
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### 9.3 事件类型

| 类型 | 说明 |
|------|------|
| `agent_response` | Agent 响应 |
| `status_update` | 状态更新 |
| `notification` | 通知消息 |

## 10. SDK 支持

### 10.1 Python SDK

```python
from opspilot import OpsPilotClient

client = OpsPilotClient(
    base_url="http://localhost:8000",
    api_key="your_api_key"
)

# 创建项目
project = client.projects.create(
    name="My Project",
    description="Project description"
)

# 与 Agent 对话
response = client.deerflow.chat(
    message="分析这个 Bug",
    thread_id="thread_123"
)
```

### 10.2 TypeScript SDK

```typescript
import { OpsPilotClient } from '@opspilot/sdk';

const client = new OpsPilotClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

// 创建项目
const project = await client.projects.create({
  name: 'My Project',
  description: 'Project description'
});
```

---

*文档版本: 1.0*
