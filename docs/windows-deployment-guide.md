# OpsPilot Windows 本地部署指南

本文档提供在 Windows 环境下部署 OpsPilot 运维领航的详细步骤。

---

## 方式一：使用 Docker Desktop（推荐）

Docker 方式是最简单的部署方法，所有服务打包在容器中，一键启动。

### 1. 系统要求

| 要求 | 说明 |
|------|------|
| 操作系统 | Windows 10/11 64位（专业版、企业版或教育版） |
| 内存 | 至少 8GB，推荐 16GB |
| 硬盘 | 至少 20GB 可用空间 |
| CPU | 支持虚拟化（Intel VT-x 或 AMD-V） |

### 2. 安装 Docker Desktop

#### 2.1 启用 Windows 功能

1. 按 `Win + X`，选择 **Windows PowerShell (管理员)**
2. 执行以下命令启用 WSL 2：

```powershell
# 启用 WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

3. **重启电脑**

4. 下载并安装 WSL 2 Linux 内核更新包：
   - 下载地址：https://aka.ms/wsl2kernel
   - 双击安装

5. 设置 WSL 2 为默认版本：

```powershell
wsl --set-default-version 2
```

#### 2.2 安装 Docker Desktop

1. 下载 Docker Desktop：
   - 官网：https://www.docker.com/products/docker-desktop/
   - 选择 **Windows** 版本

2. 双击安装程序 `Docker Desktop Installer.exe`

3. 安装选项中确保勾选：
   - ✅ Use WSL 2 instead of Hyper-V
   - ✅ Add shortcut to desktop

4. 点击 **Install**，等待安装完成

5. 安装完成后点击 **Close and restart**

#### 2.3 配置 Docker Desktop

1. 重启后，Docker Desktop 会自动启动
2. 接受服务条款
3. 跳过或完成教程
4. 点击右上角 **设置图标** ⚙️
5. 进入 **Resources > WSL Integration**
6. 确保启用了 WSL 集成

### 3. 安装 Git

1. 下载 Git for Windows：
   - 官网：https://git-scm.com/download/win
   - 选择 **64-bit Git for Windows Setup**

2. 双击安装，使用默认选项即可

3. 验证安装：

```powershell
git --version
# 应显示类似：git version 2.42.0.windows.1
```

### 4. 克隆项目

打开 **PowerShell** 或 **Git Bash**：

```powershell
# 选择一个工作目录（例如 D:\Projects）
cd D:\Projects

# 克隆 OpsPilot
git clone https://github.com/fujincursor/OpsPilot.git

# 进入项目目录
cd OpsPilot

# 克隆 DeerFlow（用于 AI Agent 功能）
git clone https://github.com/fujincursor/deer-flow-study.git deerflow
```

### 5. 配置环境变量

```powershell
# 复制环境变量模板
copy .env.example .env

# 用记事本打开编辑
notepad .env
```

在 `.env` 文件中配置以下内容：

```env
# ============ 必填配置 ============

# 应用配置
APP_NAME=OpsPilot
APP_ENV=development
DEBUG=true
SECRET_KEY=your-random-secret-key-at-least-32-chars

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============ LLM API Keys（至少配置一个）============

# OpenAI（推荐）
OPENAI_API_KEY=sk-your-openai-api-key

# 或 DeepSeek（国内推荐，便宜）
# DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 或 Anthropic Claude
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# ============ 可选配置 ============

# 搜索功能（可选）
# TAVILY_API_KEY=tvly-your-tavily-api-key

# 数据库（Docker 模式下使用默认配置即可）
# DATABASE_URL=postgresql://opspilot:opspilot@postgres:5432/opspilot
```

保存并关闭文件。

### 6. 启动服务

```powershell
# 确保 Docker Desktop 正在运行（系统托盘有鲸鱼图标）

# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 等待约 2-3 分钟，首次启动需要下载镜像
```

查看启动状态：

```powershell
# 查看容器状态
docker-compose -f docker/docker-compose.yml ps

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f

# 按 Ctrl+C 退出日志查看
```

### 7. 验证部署

打开浏览器访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:5173 | OpsPilot Web 界面 |
| 后端 API | http://localhost:8000 | FastAPI 后端 |
| API 文档 | http://localhost:8000/docs | Swagger 文档 |
| 健康检查 | http://localhost:8000/health | 服务健康状态 |

### 8. 常用 Docker 命令

```powershell
# 停止服务
docker-compose -f docker/docker-compose.yml down

# 重启服务
docker-compose -f docker/docker-compose.yml restart

# 查看后端日志
docker-compose -f docker/docker-compose.yml logs backend

# 查看前端日志
docker-compose -f docker/docker-compose.yml logs frontend

# 进入后端容器
docker-compose -f docker/docker-compose.yml exec backend bash

# 清理所有数据（谨慎操作）
docker-compose -f docker/docker-compose.yml down -v
```

### 9. 故障排除

#### Docker Desktop 启动失败

1. 检查 BIOS 中虚拟化是否启用（Intel VT-x / AMD-V）
2. 重新运行 WSL 安装命令
3. 重启电脑

#### 端口被占用

修改 `docker/docker-compose.yml` 中的端口映射：

```yaml
# 例如将 5173 改为 3000
ports:
  - "3000:5173"
```

#### 镜像下载慢

配置 Docker 镜像加速器：

1. 打开 Docker Desktop 设置
2. 进入 **Docker Engine**
3. 添加镜像配置：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

4. 点击 **Apply & Restart**

---

## 方式二：本地直接运行（无 Docker）

适合开发调试，资源占用更少，但配置相对复杂。

### 1. 系统要求

| 要求 | 说明 |
|------|------|
| 操作系统 | Windows 10/11 |
| 内存 | 至少 4GB |
| 硬盘 | 至少 5GB 可用空间 |

### 2. 安装 Python

#### 2.1 下载 Python

1. 访问 https://www.python.org/downloads/
2. 下载 **Python 3.11.x** 或更高版本（推荐 3.11）
3. 选择 **Windows installer (64-bit)**

#### 2.2 安装 Python

1. 双击安装程序
2. **重要**：勾选 ✅ **Add Python to PATH**
3. 点击 **Customize installation**
4. 勾选所有可选功能
5. 在高级选项中勾选：
   - ✅ Install for all users
   - ✅ Add Python to environment variables
6. 点击 **Install**

#### 2.3 验证安装

打开 **PowerShell**：

```powershell
python --version
# 应显示：Python 3.11.x

pip --version
# 应显示：pip 23.x.x
```

### 3. 安装 Node.js

#### 3.1 下载 Node.js

1. 访问 https://nodejs.org/
2. 下载 **LTS** 版本（推荐 18.x 或 20.x）
3. 选择 **Windows Installer (.msi) 64-bit**

#### 3.2 安装 Node.js

1. 双击安装程序
2. 接受协议，使用默认选项
3. 勾选 **Automatically install the necessary tools**（可选）
4. 点击 **Install**

#### 3.3 验证安装

```powershell
node --version
# 应显示：v18.x.x 或 v20.x.x

npm --version
# 应显示：9.x.x 或 10.x.x
```

### 4. 安装 Git

1. 下载：https://git-scm.com/download/win
2. 安装，使用默认选项
3. 验证：

```powershell
git --version
```

### 5. 克隆项目

```powershell
# 选择工作目录
cd D:\Projects

# 克隆项目
git clone https://github.com/fujincursor/OpsPilot.git
cd OpsPilot

# 克隆 DeerFlow（可选，用于完整 Agent 功能）
git clone https://github.com/fujincursor/deer-flow-study.git deerflow
```

### 6. 配置环境变量

```powershell
# 复制模板
copy .env.example .env

# 编辑配置
notepad .env
```

配置内容（与 Docker 方式相同）：

```env
# 应用配置
APP_NAME=OpsPilot
APP_ENV=development
DEBUG=true
SECRET_KEY=your-random-secret-key-at-least-32-chars

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-chars

# LLM API Key（至少配置一个）
OPENAI_API_KEY=sk-your-openai-api-key

# 数据库（本地模式使用 SQLite）
DATABASE_URL=sqlite:///./opspilot.db
```

### 7. 安装后端依赖

打开 **PowerShell**（推荐以管理员身份运行）：

```powershell
# 进入后端目录
cd D:\Projects\OpsPilot\backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果报错"无法加载文件...因为在此系统上禁止运行脚本"，执行：
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 升级 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

等待安装完成（可能需要几分钟）。

### 8. 安装前端依赖

打开**新的 PowerShell 窗口**：

```powershell
# 进入前端目录
cd D:\Projects\OpsPilot\frontend

# 安装依赖
npm install
```

等待安装完成。

### 9. 启动后端服务

在**后端 PowerShell 窗口**中：

```powershell
# 确保在 backend 目录，且虚拟环境已激活
cd D:\Projects\OpsPilot\backend
.\venv\Scripts\Activate.ps1

# 启动后端服务
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

看到以下输出表示启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Application startup complete.
```

**保持此窗口运行，不要关闭！**

### 10. 启动前端服务

在**前端 PowerShell 窗口**中：

```powershell
# 确保在 frontend 目录
cd D:\Projects\OpsPilot\frontend

# 启动前端开发服务器
npm run dev
```

看到以下输出表示启动成功：

```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
  ➜  press h + enter to show help
```

**保持此窗口运行，不要关闭！**

### 11. 验证部署

打开浏览器访问：

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

### 12. 创建启动脚本（可选）

为了方便日后启动，创建批处理脚本。

#### 创建 `start-backend.bat`

在项目根目录创建文件 `start-backend.bat`：

```batch
@echo off
echo Starting OpsPilot Backend...
cd /d D:\Projects\OpsPilot\backend
call venv\Scripts\activate.bat
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
pause
```

#### 创建 `start-frontend.bat`

在项目根目录创建文件 `start-frontend.bat`：

```batch
@echo off
echo Starting OpsPilot Frontend...
cd /d D:\Projects\OpsPilot\frontend
npm run dev
pause
```

#### 创建 `start-all.bat`

在项目根目录创建文件 `start-all.bat`：

```batch
@echo off
echo Starting OpsPilot...
start "OpsPilot Backend" cmd /k "cd /d D:\Projects\OpsPilot\backend && venv\Scripts\activate.bat && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3
start "OpsPilot Frontend" cmd /k "cd /d D:\Projects\OpsPilot\frontend && npm run dev"
echo.
echo OpsPilot is starting...
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo.
pause
```

以后只需双击 `start-all.bat` 即可启动所有服务。

### 13. 故障排除

#### Python 命令找不到

1. 重新运行 Python 安装程序
2. 选择 **Modify**
3. 确保勾选 **Add Python to environment variables**

或手动添加环境变量：
1. 右键 **此电脑** → **属性** → **高级系统设置**
2. 点击 **环境变量**
3. 在 **Path** 中添加 Python 安装路径

#### npm 命令失败

以管理员身份运行 PowerShell：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 端口被占用

查找并关闭占用端口的进程：

```powershell
# 查找占用 8000 端口的进程
netstat -ano | findstr :8000

# 根据 PID 关闭进程
taskkill /PID <进程ID> /F
```

或修改启动端口：

```powershell
# 后端使用其他端口
uvicorn src.main:app --reload --port 8001

# 前端使用其他端口
npm run dev -- --port 3000
```

#### 依赖安装失败

```powershell
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# npm 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

---

## 两种方式对比

| 特性 | Docker 方式 | 本地运行方式 |
|------|------------|-------------|
| 安装复杂度 | 低（一键启动） | 中（需手动配置） |
| 资源占用 | 较高（需要 8GB+ 内存） | 较低（4GB 即可） |
| 环境隔离 | 完全隔离 | 共享系统环境 |
| 适合场景 | 快速体验、生产部署 | 开发调试、学习 |
| 数据库 | PostgreSQL（内置） | SQLite（轻量） |
| 启动速度 | 首次慢，后续快 | 快 |

---

## 下一步

1. **配置 LLM API Key**：至少配置一个（OpenAI/DeepSeek/Anthropic）
2. **访问前端**：http://localhost:5173
3. **测试 API**：http://localhost:8000/docs
4. **阅读文档**：`docs/deerflow-integration.md`

如有问题，请查看项目 README 或提交 Issue。
