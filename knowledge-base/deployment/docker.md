# Docker 部署指南

## 1. 概述

本文档介绍如何使用 Docker 部署 OpsPilot。

## 2. 前置条件

### 2.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **CPU** | 2 核 | 4 核+ |
| **内存** | 4GB | 8GB+ |
| **磁盘** | 20GB | 50GB+ |
| **Docker** | 20.10+ | 最新版 |
| **Docker Compose** | 2.0+ | 最新版 |

### 2.2 网络要求

| 端口 | 服务 | 说明 |
|------|------|------|
| 3000 | 前端 | Web 界面 |
| 8000 | 后端 | API 服务 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存 |

## 3. 快速部署

### 3.1 获取代码

```bash
git clone https://github.com/fujincursor/OpsPilot.git
cd OpsPilot
```

### 3.2 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://opspilot:password@db:5432/opspilot
REDIS_URL=redis://redis:6379

# AI 模型配置
OPENAI_API_KEY=sk-your-api-key
DEEPSEEK_API_KEY=your-deepseek-key

# 应用配置
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### 3.3 启动服务

```bash
docker-compose up -d
```

### 3.4 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 测试 API
curl http://localhost:8000/api/v1/health
```

访问 http://localhost:3000 进入 Web 界面。

## 4. Docker Compose 配置

### 4.1 完整配置示例

```yaml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://opspilot:password@db:5432/opspilot
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  # 数据库
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=opspilot
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=opspilot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U opspilot"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 4.2 前端 Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

### 4.3 后端 Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 5. 生产环境配置

### 5.1 使用外部数据库

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@your-db-host:5432/opspilot
```

### 5.2 HTTPS 配置

使用 Traefik 或 Nginx 作为反向代理：

```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  frontend:
    labels:
      - "traefik.http.routers.frontend.rule=Host(`opspilot.example.com`)"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```

### 5.3 资源限制

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## 6. 数据持久化

### 6.1 数据卷

```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  uploads:
    driver: local
```

### 6.2 备份策略

```bash
# 备份数据库
docker-compose exec db pg_dump -U opspilot opspilot > backup.sql

# 恢复数据库
docker-compose exec -T db psql -U opspilot opspilot < backup.sql
```

## 7. 日志管理

### 7.1 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务
docker-compose logs backend

# 实时日志
docker-compose logs -f --tail=100
```

### 7.2 日志驱动配置

```yaml
services:
  backend:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## 8. 健康检查

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 9. 升级流程

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 运行数据库迁移
docker-compose exec backend alembic upgrade head
```

## 10. 常见问题

### Q1: 容器启动失败

检查日志：
```bash
docker-compose logs backend
```

常见原因：
- 端口被占用
- 环境变量未配置
- 数据库连接失败

### Q2: 数据库连接超时

确保数据库服务已启动：
```bash
docker-compose ps db
docker-compose logs db
```

### Q3: 内存不足

增加 Docker 内存限制或优化资源配置。

---

*文档版本: 1.0*
