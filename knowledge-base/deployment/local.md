# 本地开发部署指南

## 1. 概述

本文档介绍如何在本地环境进行 OpsPilot 开发部署。

## 2. 前置条件

### 2.1 软件要求

| 软件 | 版本要求 | 安装方式 |
|------|----------|----------|
| **Python** | 3.11+ | python.org |
| **Node.js** | 20+ | nodejs.org |
| **PostgreSQL** | 15+ | postgresql.org |
| **Redis** | 7+ | redis.io |
| **Git** | 最新版 | git-scm.com |

### 2.2 可选工具

- **VS Code**: 推荐的 IDE
- **DBeaver**: 数据库管理工具
- **Postman**: API 测试工具

## 3. 环境搭建

### 3.1 克隆代码

```bash
git clone https://github.com/fujincursor/OpsPilot.git
cd OpsPilot
```

### 3.2 后端设置

#### 创建虚拟环境

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# 数据库
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/opspilot

# Redis
REDIS_URL=redis://localhost:6379

# AI API Keys
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=your-deepseek-key

# 应用配置
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
```

#### 初始化数据库

```bash
# 创建数据库
createdb opspilot

# 运行迁移
alembic upgrade head
```

#### 启动后端

```bash
uvicorn src.main:app --reload --port 8000
```

### 3.3 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
```

编辑 `.env.local`：

```env
VITE_API_URL=http://localhost:8000
```

启动前端：

```bash
npm run dev
```

## 4. 开发工作流

### 4.1 代码结构

```
OpsPilot/
├── backend/
│   ├── src/
│   │   ├── api/          # API 路由
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务逻辑
│   │   └── main.py       # 入口
│   ├── tests/            # 测试
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # 组件
│   │   ├── pages/        # 页面
│   │   └── App.tsx       # 入口
│   └── package.json
└── docker-compose.yml
```

### 4.2 开发命令

```bash
# 后端
cd backend
uvicorn src.main:app --reload          # 开发服务器
pytest                                   # 运行测试
ruff check .                            # 代码检查
ruff format .                           # 代码格式化

# 前端
cd frontend
npm run dev                              # 开发服务器
npm run build                            # 构建
npm run lint                             # 代码检查
npm run test                             # 运行测试
```

### 4.3 数据库操作

```bash
# 创建迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 5. 调试技巧

### 5.1 后端调试

VS Code 配置 (`.vscode/launch.json`)：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

### 5.2 前端调试

使用浏览器开发者工具：
- React Developer Tools
- Network 面板查看 API 请求

### 5.3 日志级别

```python
# backend/src/core/config.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 6. 测试

### 6.1 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_projects.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 6.2 前端测试

```bash
cd frontend

# 运行测试
npm run test

# 监视模式
npm run test:watch
```

## 7. 代码规范

### 7.1 后端规范

- 使用 Ruff 进行代码检查
- 遵循 PEP 8 规范
- 类型注解完整

```bash
ruff check .
ruff format .
```

### 7.2 前端规范

- 使用 ESLint + Prettier
- 遵循 TypeScript 最佳实践

```bash
npm run lint
npm run format
```

## 8. Mock 模式

当 AI 服务不可用时，可以使用 Mock 模式：

```env
# .env
USE_MOCK_AI=true
```

Mock 模式返回预定义的响应，方便开发调试。

## 9. 常见问题

### Q1: 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000

# 终止进程
kill -9 <PID>
```

### Q2: 数据库连接失败

确保 PostgreSQL 正在运行：

```bash
# Windows
net start postgresql-x64-15

# Linux
sudo systemctl start postgresql
```

### Q3: npm install 失败

```bash
# 清理缓存
npm cache clean --force

# 删除 node_modules
rm -rf node_modules package-lock.json
npm install
```

### Q4: Python 依赖冲突

```bash
# 重新创建虚拟环境
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 10. IDE 配置

### 10.1 VS Code 推荐扩展

- Python
- Pylance
- ESLint
- Prettier
- GitLens

### 10.2 推荐设置

```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

*文档版本: 1.0*
