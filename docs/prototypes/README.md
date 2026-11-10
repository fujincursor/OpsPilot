# 运维 Agent 生产系统 - 页面原型索引

本目录包含基于 **DeerFlow 2.0 架构**的 HTML 页面原型，遵循 [《页面原型风格规范》](../页面原型风格规范.md)。

---

## 🆕 DeerFlow 新增原型

### Phase 1: 核心交互重设计

| 模块 | 页面 | 说明 |
|------|------|------|
| **对话式入口** | [chat/welcome.html](chat/welcome.html) | 新会话欢迎状态 |
| | [chat/index.html](chat/index.html) | 对话主界面（消息流） |
| | [chat/approval.html](chat/approval.html) | HITL 审批卡片示例 |

### Phase 2: 新增功能页面

| 模块 | 页面 | 说明 |
|------|------|------|
| **执行监控** | [monitor/index.html](monitor/index.html) | Agent 执行监控主页 |
| | [monitor/task-detail.html](monitor/task-detail.html) | 任务执行详情 |
| **配置管理** | [m1/project-settings-skills.html](m1/project-settings-skills.html) | Skills 配置 |
| | [m1/project-settings-sandbox.html](m1/project-settings-sandbox.html) | Sandbox 配置 |

---

## 推荐访问顺序（单点登录流程）

1. **[统一登录](portal/login.html)** → 模拟登录，任意输入即可进入工作台
2. **[工作台](portal/index.html)** → 展示功能模块入口
3. **[对话入口](chat/welcome.html)** → 🆕 DeerFlow 对话式交互
4. **[执行监控](monitor/index.html)** → 🆕 Agent 执行状态监控

---

## 统一入口（Portal）

| 页面 | 文件 | 说明 |
|------|------|------|
| 登录 | [portal/login.html](portal/login.html) | 统一登录页 |
| 工作台 | [portal/index.html](portal/index.html) | 统一入口工作台 |

---

## 项目管理（M1）

| 页面 | 文件 | 说明 |
|------|------|------|
| 项目列表 | [m1/project-list.html](m1/project-list.html) | 项目管理首页 |
| 新建项目 | [m1/project-new.html](m1/project-new.html) | 创建项目表单 |
| 项目详情 | [m1/project-detail.html](m1/project-detail.html) | 项目概览 |
| 基本信息 | [m1/project-settings-basic.html](m1/project-settings-basic.html) | 设置 - 基本信息 |
| Agent 配置 | [m1/project-settings-agent.html](m1/project-settings-agent.html) | 设置 - Agent |
| Skills 配置 | [m1/project-settings-skills.html](m1/project-settings-skills.html) | 🆕 设置 - Skills |
| Sandbox 配置 | [m1/project-settings-sandbox.html](m1/project-settings-sandbox.html) | 🆕 设置 - Sandbox |
| 成员管理 | [m1/project-settings-members.html](m1/project-settings-members.html) | 设置 - 成员 |
| 高级 | [m1/project-settings-advanced.html](m1/project-settings-advanced.html) | 设置 - 高级 |

---

## 对话式入口（Chat）🆕

| 页面 | 文件 | 说明 |
|------|------|------|
| 欢迎页 | [chat/welcome.html](chat/welcome.html) | 新会话欢迎状态 |
| 对话主页 | [chat/index.html](chat/index.html) | 消息流与知识检索 |
| HITL 审批 | [chat/approval.html](chat/approval.html) | 内嵌审批卡片 |

---

## Agent 执行监控（Monitor）🆕

| 页面 | 文件 | 说明 |
|------|------|------|
| 监控主页 | [monitor/index.html](monitor/index.html) | 任务概览与卡片 |
| 任务详情 | [monitor/task-detail.html](monitor/task-detail.html) | 流程图与日志 |

---

## 知识库（M3）

| 页面 | 文件 | 说明 |
|------|------|------|
| 知识概览 | [m3/knowledge-overview.html](m3/knowledge-overview.html) | 知识库首页 |
| 文档列表 | [m3/knowledge-doc-list.html](m3/knowledge-doc-list.html) | 文档管理 |
| 文档详情 | [m3/knowledge-doc-detail.html](m3/knowledge-doc-detail.html) | 文档查看 |
| 代码索引 | [m3/knowledge-code-index.html](m3/knowledge-code-index.html) | 代码索引管理 |

---

## 其他模块

各模块目录内均有 README 与详细页面列表，可进入后按需查看：

- [m2/](m2/) - 项目信息维护
- [m4/](m4/) - 需求工单（将被对话式入口替代）
- [m5/](m5/) - Bug 工单
- [m6/](m6/) - 新需求
- [m7/](m7/) - Review 工作台（将被 HITL 卡片替代）
- [m8/](m8/) - 代码生成
- [m9/](m9/) - 测试报告

---

## 设计文档

- [DeerFlow原型设计-索引.md](../DeerFlow原型设计-索引.md) - 原型设计总览
- [DeerFlow架构重设计-运维Agent生产系统.md](../DeerFlow架构重设计-运维Agent生产系统.md) - 架构设计
- [页面原型风格规范.md](../页面原型风格规范.md) - 样式规范
