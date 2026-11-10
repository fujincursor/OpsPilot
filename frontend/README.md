# OpsPilot Frontend

OpsPilot 运维领航前端应用，基于 React + TypeScript + Vite 构建。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **样式**: Tailwind CSS
- **路由**: React Router v6

## 项目结构

```
frontend/
├── src/
│   ├── App.tsx                 # 应用入口，路由配置
│   ├── main.tsx                # React 挂载入口
│   ├── index.css               # 全局样式入口
│   ├── components/
│   │   ├── Layout/             # 布局组件
│   │   │   ├── Header.tsx      # 顶部导航栏
│   │   │   ├── Sidebar.tsx     # 侧边栏（对话历史）
│   │   │   └── index.tsx       # 布局容器
│   │   └── Chat/               # 对话组件
│   │       ├── ChatWindow.tsx  # 对话窗口主组件
│   │       ├── MessageList.tsx # 消息列表
│   │       ├── MessageInput.tsx# 消息输入框
│   │       └── index.tsx       # 导出文件
│   ├── pages/
│   │   ├── Home.tsx            # 首页/工作台
│   │   └── Chat.tsx            # 对话页面
│   └── styles/
│       └── globals.css         # 全局 CSS 变量
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 开发指南

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:3000 启动。

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 核心组件说明

### Layout 组件

- **Header**: 顶部导航栏，包含 Logo、导航菜单、Agent 状态指示器和用户头像
- **Sidebar**: 对话侧边栏，包含项目选择器和历史会话列表
- **Layout**: 布局容器，根据路由自动显示/隐藏侧边栏

### Chat 组件

- **ChatWindow**: 对话窗口主组件，管理消息状态和用户交互
- **MessageList**: 消息列表组件，支持多种消息类型：
  - 用户消息（右对齐蓝底）
  - Agent 消息（左对齐白底）
  - 知识检索卡片
  - 分类结果卡片
  - Sub-Agent 执行进度卡片
- **MessageInput**: 消息输入组件，支持 Enter 发送和 Shift+Enter 换行

### 页面组件

- **Home**: 工作台首页，显示统计数据、快捷入口和最近活动
- **Chat**: 对话页面，集成 ChatWindow 组件

## 设计规范

本项目 UI 设计遵循 `docs/prototypes/chat/` 目录下的原型设计：

- 配色方案：主色 #4F46E5 (Indigo)
- 消息气泡：用户消息蓝底右对齐，Agent 消息白底左对齐
- 卡片组件：知识检索、分类结果、执行步骤等

## 路由配置

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | Home | 工作台首页 |
| `/chat` | Chat | 新建对话 |
| `/chat/:sessionId` | Chat | 查看/继续会话 |

## 后续计划

- [ ] 集成后端 API
- [ ] WebSocket 实时消息
- [ ] HITL 审批卡片组件
- [ ] 项目管理页面
- [ ] 监控面板页面
