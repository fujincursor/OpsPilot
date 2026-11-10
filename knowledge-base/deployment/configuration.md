# 配置指南

## 1. 概述

本文档详细说明 OpsPilot 的配置选项。

## 2. 环境变量

### 2.1 必需配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | 数据库连接 | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | JWT 密钥 | 随机字符串，至少 32 字符 |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |

### 2.2 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `REDIS_URL` | Redis 连接 | `redis://localhost:6379` |
| `DEBUG` | 调试模式 | `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `CORS_ORIGINS` | CORS 允许源 | `*` |
| `MAX_UPLOAD_SIZE` | 上传限制 | `10MB` |

### 2.3 AI 模型配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI Key | - |
| `OPENAI_MODEL` | OpenAI 模型 | `gpt-4o` |
| `DEEPSEEK_API_KEY` | DeepSeek Key | - |
| `DEEPSEEK_MODEL` | DeepSeek 模型 | `deepseek-chat` |
| `ANTHROPIC_API_KEY` | Claude Key | - |
| `USE_MOCK_AI` | Mock 模式 | `false` |

## 3. DeerFlow 配置

### 3.1 config.yaml

```yaml
# config.yaml - DeerFlow 配置

# 模型配置
models:
  primary:
    provider: openai
    model: gpt-4o
    temperature: 0.7
  fallback:
    provider: deepseek
    model: deepseek-chat
  embedding:
    provider: openai
    model: text-embedding-3-small

# Agent 配置
agents:
  lead_agent:
    name: Lead Agent
    model: primary
    max_iterations: 20
  
  sub_agents:
    researcher:
      name: Researcher
      model: primary
      skills:
        - knowledge-retrieval
    
    coder:
      name: Coder
      model: primary
      skills:
        - code-generation
        - test-execution

# 工具配置
tools:
  web_search:
    enabled: true
    provider: tavily
    api_key: ${TAVILY_API_KEY}
  
  code_execution:
    enabled: true
    sandbox_enabled: true
    timeout: 300

# Sandbox 配置
sandbox:
  mode: docker
  config:
    image: python:3.11-slim
    timeout: 300
    memory_limit: 512m
    network_mode: none

# Memory 配置
memory:
  type: redis
  config:
    url: ${REDIS_URL}
    ttl: 86400

# HITL 配置
hitl:
  enabled: true
  timeout: 86400
  notification:
    email: true
    webhook: false
```

### 3.2 Skills 配置

```yaml
# skills/requirement-analysis/SKILL.md
---
name: requirement-analysis
display_name: 需求分析
description: 分析和理解软件需求
version: 1.0.0
author: OpsPilot Team
tags:
  - analysis
  - requirements
inputs:
  - name: requirement
    type: string
    required: true
outputs:
  - name: analysis
    type: object
---
```

## 4. 数据库配置

### 4.1 PostgreSQL

```env
DATABASE_URL=postgresql://user:password@localhost:5432/opspilot
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
```

### 4.2 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "add new table"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 5. Redis 配置

```env
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
```

## 6. 日志配置

### 6.1 日志级别

| 级别 | 说明 |
|------|------|
| `DEBUG` | 详细调试信息 |
| `INFO` | 一般信息 |
| `WARNING` | 警告信息 |
| `ERROR` | 错误信息 |
| `CRITICAL` | 严重错误 |

### 6.2 日志格式

```python
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "default"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```

## 7. 安全配置

### 7.1 CORS

```env
CORS_ORIGINS=https://example.com,https://app.example.com
CORS_ALLOW_CREDENTIALS=true
```

### 7.2 JWT

```env
SECRET_KEY=your-secure-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### 7.3 Rate Limiting

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AI=20/minute
```

## 8. 前端配置

### 8.1 环境变量

```env
# .env.local
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_APP_TITLE=OpsPilot
```

### 8.2 构建配置

```javascript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

## 9. 性能调优

### 9.1 后端优化

```env
# 工作进程
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker

# 数据库连接池
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### 9.2 缓存配置

```env
# Redis 缓存
CACHE_TTL=3600
CACHE_PREFIX=opspilot:
```

## 10. 配置验证

启动时会验证配置：

```python
from src.core.config import get_settings

settings = get_settings()
settings.validate()
```

常见验证错误：
- 必需环境变量未设置
- 数据库连接失败
- API Key 无效

---

*文档版本: 1.0*
