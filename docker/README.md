# OpsPilot Docker Configuration

## 目录结构

```
docker/
├── docker-compose.yml        # 开发环境配置
├── docker-compose.prod.yml   # 生产环境配置
├── backend/
│   └── Dockerfile            # FastAPI 后端镜像
├── frontend/
│   ├── Dockerfile            # Vite 前端镜像
│   └── nginx.conf            # Nginx 配置
├── sandbox/
│   ├── Dockerfile            # 沙箱执行环境镜像
│   └── entrypoint.sh         # 沙箱入口脚本
├── init-scripts/
│   └── 01-init.sql           # PostgreSQL 初始化脚本
├── redis/
│   └── redis.conf            # Redis 配置
└── nginx/
    └── ssl/                  # SSL 证书目录
```

## 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| backend | 8000 | FastAPI 后端 API |
| frontend | 5173 (dev) / 80 (prod) | Vite 开发服务器 / Nginx |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |
| milvus | 19530 | Milvus 向量数据库 |
| minio | 9000, 9001 | MinIO 对象存储 |
| sandbox | - | 代码执行沙箱 |

## 快速开始

### 开发环境

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 启动所有服务
make up

# 3. 查看日志
make logs
```

### 生产环境

```bash
# 1. 配置生产环境变量
cp .env.example .env
# 编辑 .env 设置生产参数

# 2. 构建生产镜像
make build-prod

# 3. 启动生产环境
make prod-up
```

## 常用命令

```bash
make up           # 启动服务
make down         # 停止服务
make dev          # 开发模式（前台运行+日志）
make logs         # 查看日志
make build        # 构建镜像
make ps           # 查看容器状态
make shell-backend    # 进入后端容器
make db-shell     # 进入数据库
make test         # 运行测试
make clean        # 清理容器和数据
```

## 网络架构

```
┌─────────────────────────────────────────────────────────┐
│                   opspilot-network                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ frontend │  │ backend  │  │ postgres │  │  redis  │ │
│  │  :5173   │──│  :8000   │──│  :5432   │  │  :6379  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                      │                                   │
│              ┌───────┴───────┐                          │
│              │    milvus     │                          │
│              │    :19530     │                          │
│              └───────┬───────┘                          │
│         ┌────────────┼────────────┐                     │
│    ┌────┴────┐  ┌────┴────┐                            │
│    │  etcd   │  │  minio  │                            │
│    └─────────┘  └─────────┘                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   sandbox-network (internal)             │
│  ┌──────────┐                                           │
│  │ sandbox  │  隔离的代码执行环境                        │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
```

## 安全说明

### Sandbox 安全特性

- 无特权模式运行
- 禁用所有 Linux capabilities
- 只读文件系统
- 内存和 CPU 限制
- 隔离网络（internal network）
- 执行超时限制

### 生产环境建议

1. 修改所有默认密码
2. 启用 SSL/TLS
3. 配置防火墙规则
4. 定期备份数据库
5. 监控服务健康状态
