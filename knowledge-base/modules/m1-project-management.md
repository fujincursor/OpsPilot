# M1: 项目与 Agent 管理模块

## 1. 模块概述

项目与 Agent 管理模块是 OpsPilot 的基础管理模块，负责项目的创建、配置和管理，以及 Agent 配置的维护。

### 1.1 核心功能

- 项目 CRUD 操作
- 项目成员管理
- Agent 配置管理
- 项目级参数设置

### 1.2 模块定位

```
用户 → 项目管理 → 创建/配置项目
                      │
                      ↓
              Agent 配置 → 选择/配置 Agent
                      │
                      ↓
              其他模块 → 在项目上下文中工作
```

## 2. 项目管理

### 2.1 项目数据模型

```python
class Project:
    id: str                    # 项目唯一标识
    name: str                  # 项目名称
    description: str           # 项目描述
    status: ProjectStatus      # 项目状态
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
    owner_id: str              # 所有者 ID
    settings: ProjectSettings  # 项目设置
    agents: List[AgentConfig]  # Agent 配置
```

### 2.2 项目状态

| 状态 | 说明 | 允许操作 |
|------|------|----------|
| `active` | 活跃 | 全部操作 |
| `archived` | 归档 | 只读，可恢复 |
| `deleted` | 已删除 | 不可见 |

### 2.3 项目操作

#### 创建项目

```http
POST /api/v1/projects
Content-Type: application/json

{
  "name": "我的运维项目",
  "description": "用于管理生产环境运维需求",
  "settings": {
    "default_agent": "requirement_analyzer",
    "auto_analyze": true,
    "notification_enabled": true
  }
}
```

#### 获取项目列表

```http
GET /api/v1/projects?status=active&page=1&size=20
```

#### 更新项目

```http
PUT /api/v1/projects/{project_id}
Content-Type: application/json

{
  "name": "更新后的项目名",
  "description": "更新后的描述"
}
```

#### 删除项目

```http
DELETE /api/v1/projects/{project_id}
```

## 3. Agent 配置管理

### 3.1 Agent 类型

| Agent | 职责 | 关联 Skills |
|-------|------|-------------|
| **requirement_analyzer** | 需求分析 | requirement-analysis, knowledge-retrieval |
| **bugfix_agent** | Bug 修复 | bugfix-solution, code-generation |
| **feature_agent** | 功能设计 | feature-design, deep-research |
| **codegen_agent** | 代码生成 | code-generation, test-execution |
| **test_agent** | 测试执行 | test-execution |

### 3.2 Agent 配置模型

```python
class AgentConfig:
    name: str                  # Agent 名称
    display_name: str          # 显示名称
    description: str           # 描述
    enabled: bool              # 是否启用
    skills: List[str]          # 关联 Skills
    settings: AgentSettings    # Agent 设置
```

### 3.3 Agent 设置项

```yaml
agent_settings:
  # 模型配置
  model: gpt-4o
  temperature: 0.7
  max_tokens: 4096
  
  # 行为配置
  auto_execute: false      # 自动执行
  require_approval: true   # 需要审批
  max_iterations: 10       # 最大迭代次数
  
  # 超时配置
  timeout_seconds: 300     # 执行超时
  
  # 上下文配置
  context_window: 10       # 上下文消息数
  include_history: true    # 包含历史
```

### 3.4 Agent 管理 API

#### 获取 Agent 列表

```http
GET /api/v1/agents?project_id={project_id}
```

响应示例：
```json
{
  "agents": [
    {
      "name": "requirement_analyzer",
      "display_name": "需求分析 Agent",
      "description": "分析和分类运维需求",
      "enabled": true,
      "skills": ["requirement-analysis", "knowledge-retrieval"]
    },
    {
      "name": "bugfix_agent",
      "display_name": "Bug 修复 Agent",
      "enabled": true,
      "skills": ["bugfix-solution", "code-generation"]
    }
  ]
}
```

#### 更新 Agent 配置

```http
PUT /api/v1/agents/{agent_name}
Content-Type: application/json

{
  "enabled": true,
  "settings": {
    "model": "gpt-4o",
    "temperature": 0.5
  }
}
```

## 4. 项目上下文

### 4.1 上下文传递

项目上下文通过中间件自动注入到请求中：

```python
class ProjectContextMiddleware:
    async def __call__(self, request, call_next):
        project_id = request.headers.get("X-Project-ID")
        if project_id:
            project = await get_project(project_id)
            request.state.project = project
        return await call_next(request)
```

### 4.2 上下文使用

在服务层使用项目上下文：

```python
async def analyze_requirement(request: Request, data: dict):
    project = request.state.project
    
    # 获取项目配置的 Agent
    agent_config = project.get_agent_config("requirement_analyzer")
    
    # 使用项目级设置
    if project.settings.auto_analyze:
        return await auto_analyze(data, agent_config)
```

## 5. 项目设置

### 5.1 通用设置

| 设置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `default_agent` | string | requirement_analyzer | 默认 Agent |
| `auto_analyze` | bool | true | 自动分析需求 |
| `notification_enabled` | bool | true | 启用通知 |
| `max_requirements` | int | 1000 | 最大需求数 |

### 5.2 知识库设置

| 设置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `knowledge_required` | bool | false | 需求创建前需知识库就绪 |
| `auto_index` | bool | true | 自动索引文档 |
| `search_top_k` | int | 5 | 搜索返回数量 |

### 5.3 审核设置

| 设置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `require_review` | bool | true | 需要人工审核 |
| `review_timeout_hours` | int | 24 | 审核超时时间 |
| `auto_approve_low_risk` | bool | false | 低风险自动通过 |

## 6. 权限控制

### 6.1 项目角色

| 角色 | 权限 |
|------|------|
| **Owner** | 全部权限，可删除项目 |
| **Admin** | 管理项目设置、成员 |
| **Member** | 创建/处理需求 |
| **Viewer** | 只读访问 |

### 6.2 权限矩阵

| 操作 | Owner | Admin | Member | Viewer |
|------|-------|-------|--------|--------|
| 查看项目 | ✅ | ✅ | ✅ | ✅ |
| 编辑项目 | ✅ | ✅ | ❌ | ❌ |
| 删除项目 | ✅ | ❌ | ❌ | ❌ |
| 管理成员 | ✅ | ✅ | ❌ | ❌ |
| 配置 Agent | ✅ | ✅ | ❌ | ❌ |
| 创建需求 | ✅ | ✅ | ✅ | ❌ |

## 7. 最佳实践

### 7.1 项目组织建议

1. **按业务线划分项目**
   - 每个业务系统一个项目
   - 便于知识隔离和权限管理

2. **合理配置 Agent**
   - 根据实际需求启用 Agent
   - 调整 Agent 参数以优化效果

3. **定期维护**
   - 清理过期需求
   - 归档已完成项目

### 7.2 Agent 配置建议

1. **选择合适的模型**
   - 简单任务用快速模型
   - 复杂任务用能力强的模型

2. **调整温度参数**
   - 需要创意时提高温度
   - 需要精确时降低温度

3. **设置合理超时**
   - 根据任务复杂度设置
   - 避免资源浪费

## 8. 常见问题

### Q1: 如何迁移项目？

项目数据可以通过 API 导出和导入：

```bash
# 导出
curl -X GET /api/v1/projects/{id}/export > project.json

# 导入
curl -X POST /api/v1/projects/import -d @project.json
```

### Q2: Agent 配置不生效？

检查项：
1. 确认 Agent 已启用
2. 确认 Skills 已正确关联
3. 检查 config.yaml 配置
4. 重启服务使配置生效

### Q3: 如何批量管理项目？

使用项目管理 API：

```python
# 批量归档
for project_id in project_ids:
    await archive_project(project_id)
```

---

*文档版本: 1.0*
*所属模块: M1 - 项目与 Agent 管理*
