# 项目管理 API

## 概述

项目管理 API 提供项目的 CRUD 操作以及项目配置管理功能。

**基础路径**: `/api/v1/projects`

## 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/projects` | 获取项目列表 |
| POST | `/projects` | 创建项目 |
| GET | `/projects/{id}` | 获取项目详情 |
| PUT | `/projects/{id}` | 更新项目 |
| DELETE | `/projects/{id}` | 删除项目 |
| GET | `/projects/{id}/agents` | 获取项目 Agent |
| PUT | `/projects/{id}/config` | 更新项目配置 |

---

## GET /projects

获取项目列表。

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `page` | int | 否 | 页码，默认 1 |
| `size` | int | 否 | 每页数量，默认 20 |
| `status` | string | 否 | 状态过滤 |
| `search` | string | 否 | 搜索关键字 |

### 请求示例

```http
GET /api/v1/projects?page=1&size=10&status=active
Authorization: Bearer <token>
```

### 响应示例

```json
{
  "data": [
    {
      "id": "proj_abc123",
      "name": "用户管理系统",
      "description": "用户注册、登录、权限管理",
      "status": "active",
      "agent_count": 3,
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 10,
    "total": 25,
    "total_pages": 3
  }
}
```

---

## POST /projects

创建新项目。

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 项目名称 |
| `description` | string | 否 | 项目描述 |
| `repository_url` | string | 否 | 代码仓库 URL |
| `config` | object | 否 | 项目配置 |

### 请求示例

```http
POST /api/v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "电商平台",
  "description": "电商系统后端服务",
  "repository_url": "https://github.com/org/ecommerce",
  "config": {
    "language": "python",
    "framework": "fastapi"
  }
}
```

### 响应示例

```json
{
  "data": {
    "id": "proj_xyz789",
    "name": "电商平台",
    "description": "电商系统后端服务",
    "repository_url": "https://github.com/org/ecommerce",
    "status": "active",
    "config": {
      "language": "python",
      "framework": "fastapi"
    },
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

---

## GET /projects/{id}

获取项目详情。

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 项目 ID |

### 请求示例

```http
GET /api/v1/projects/proj_abc123
Authorization: Bearer <token>
```

### 响应示例

```json
{
  "data": {
    "id": "proj_abc123",
    "name": "用户管理系统",
    "description": "用户注册、登录、权限管理",
    "repository_url": "https://github.com/org/user-system",
    "status": "active",
    "config": {
      "language": "python",
      "framework": "fastapi",
      "review_required": true
    },
    "stats": {
      "total_requirements": 45,
      "completed_requirements": 38,
      "agents": 3
    },
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## PUT /projects/{id}

更新项目信息。

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 项目 ID |

### 请求体

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | 否 | 项目名称 |
| `description` | string | 否 | 项目描述 |
| `status` | string | 否 | 状态 |

### 请求示例

```http
PUT /api/v1/projects/proj_abc123
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "用户管理系统 V2",
  "description": "更新后的描述"
}
```

---

## DELETE /projects/{id}

删除项目。

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 项目 ID |

### 请求示例

```http
DELETE /api/v1/projects/proj_abc123
Authorization: Bearer <token>
```

### 响应

```
HTTP/1.1 204 No Content
```

---

## GET /projects/{id}/agents

获取项目的 Agent 列表。

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 项目 ID |

### 请求示例

```http
GET /api/v1/projects/proj_abc123/agents
Authorization: Bearer <token>
```

### 响应示例

```json
{
  "data": [
    {
      "id": "agent_001",
      "name": "需求分析 Agent",
      "type": "requirement_analyst",
      "status": "active",
      "skills": ["requirement-analysis"]
    },
    {
      "id": "agent_002",
      "name": "代码生成 Agent",
      "type": "code_generator",
      "status": "active",
      "skills": ["code-generation"]
    }
  ]
}
```

---

## PUT /projects/{id}/config

更新项目配置。

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 项目 ID |

### 请求体

| 字段 | 类型 | 说明 |
|------|------|------|
| `language` | string | 编程语言 |
| `framework` | string | 框架 |
| `review_required` | bool | 是否需要审核 |
| `auto_test` | bool | 自动运行测试 |

### 请求示例

```http
PUT /api/v1/projects/proj_abc123/config
Authorization: Bearer <token>
Content-Type: application/json

{
  "language": "python",
  "framework": "fastapi",
  "review_required": true,
  "auto_test": true
}
```

---

*文档版本: 1.0*
