# OpsPilot Backend

OpsPilot 运维领航后端服务，基于 FastAPI 构建。

## 技术栈

- **FastAPI** - 高性能异步 Web 框架
- **Pydantic** - 数据验证和序列化
- **Uvicorn** - ASGI 服务器

## 快速开始

### 环境要求

- Python 3.10+

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 运行服务

```bash
# 开发模式
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## API 接口

### 健康检查

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 服务健康状态 |
| GET | `/health/ready` | 就绪检查 |
| GET | `/health/live` | 存活检查 |

### 项目管理 (v1)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/projects` | 获取项目列表 |
| GET | `/api/v1/projects/{id}` | 获取项目详情 |
| POST | `/api/v1/projects` | 创建项目 |
| PUT | `/api/v1/projects/{id}` | 更新项目 |
| DELETE | `/api/v1/projects/{id}` | 删除项目 |

## 项目结构

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py    # 健康检查
│   │       └── projects.py  # 项目管理 API
│   ├── models/
│   │   ├── __init__.py
│   │   └── project.py       # 项目模型
│   └── services/
│       ├── __init__.py
│       └── project_service.py
├── requirements.txt
└── README.md
```

## 配置

通过环境变量或 `.env` 文件配置：

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `APP_NAME` | OpsPilot | 应用名称 |
| `APP_VERSION` | 0.1.0 | 应用版本 |
| `DEBUG` | false | 调试模式 |
| `CORS_ORIGINS` | localhost:3000,localhost:5173 | CORS 允许的源 |

## 开发

### 代码风格

项目遵循 PEP 8 规范，建议使用以下工具：

```bash
# 格式化
pip install black isort
black src/
isort src/

# 类型检查
pip install mypy
mypy src/
```
