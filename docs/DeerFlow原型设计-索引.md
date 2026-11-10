# DeerFlow 原型设计索引

本目录包含基于 DeerFlow 架构的页面原型设计稿，按优先级分为 Phase 1-3。

---

## 设计概览

### 优化优先级矩阵

```
                      高业务价值
                          │
     Phase 1              │              Phase 2
     (必须)               │              (推荐)
                          │
   • 对话式需求入口       │         • Agent 执行监控
   • HITL 审批卡片        │         • Skills/Sandbox 配置
                          │
  ────────────────────────┼────────────────────────
                          │
     保持现状             │              Phase 3
                          │              (可选)
                          │
   • M1 项目列表          │         • 知识引用展示
   • M2 项目信息          │         • Sandbox 执行预览
   • M9 测试报告          │
                          │
     低改动量 ────────────┼──────────── 高改动量
                      低业务价值
```

---

## Phase 1: 核心交互重设计（必须）

核心交互模式变化，直接影响用户体验。

| 文档 | 说明 | 工作量 |
|------|------|--------|
| [Phase1-对话式需求入口](DeerFlow原型设计-Phase1-对话式需求入口.md) | 将表单式提交改为对话式交互 | 3-5 天 |
| [Phase1-HITL审批卡片](DeerFlow原型设计-Phase1-HITL审批卡片.md) | 将独立审批页改为内嵌审批卡片 | 2-3 天 |

### Phase 1 页面清单

```
📁 Phase 1
├── 对话式需求入口
│   ├── chat/index.html          # 对话主页面
│   ├── chat/empty-state.html    # 新会话欢迎状态
│   ├── chat/analyzing.html      # Agent 分析中状态
│   ├── chat/complete.html       # 分析完成带结果
│   └── chat/history.html        # 历史会话列表
│
└── HITL 审批卡片
    ├── components/approval-card-plan.html   # 方案审批卡片
    ├── components/approval-card-code.html   # 代码审批卡片
    ├── components/approval-card-test.html   # 测试审批卡片
    ├── components/approval-reject-modal.html # 驳回弹窗
    ├── components/approval-history.html     # 审批历史组件
    └── components/timeout-reminder.html     # 超时提醒组件
```

---

## Phase 2: 新增关键页面（推荐）

新增 DeerFlow 架构特有的功能页面。

| 文档 | 说明 | 工作量 |
|------|------|--------|
| [Phase2-Agent执行监控](DeerFlow原型设计-Phase2-Agent执行监控.md) | Agent 执行状态实时监控 | 2-3 天 |
| [Phase2-Skills与Sandbox配置](DeerFlow原型设计-Phase2-Skills与Sandbox配置.md) | Skills 和 Sandbox 配置页签 | 1-2 天 |

### Phase 2 页面清单

```
📁 Phase 2
├── Agent 执行监控
│   ├── monitor/index.html       # 监控主页
│   ├── monitor/task-detail.html # 任务详情页
│   ├── monitor/history.html     # 执行历史页
│   ├── components/task-card.html    # 任务卡片组件
│   ├── components/flow-diagram.html # 流程图组件
│   └── components/log-viewer.html   # 日志查看器组件
│
└── Skills 与 Sandbox 配置
    ├── m1/settings-skills.html      # Skills 配置页
    ├── m1/settings-sandbox.html     # Sandbox 配置页
    ├── components/skill-card.html   # Skill 卡片组件
    ├── components/add-skill-modal.html    # 添加 Skill 弹窗
    ├── components/skill-config-modal.html # Skill 配置弹窗
    └── components/sandbox-test-result.html # 配置测试结果弹窗
```

---

## Phase 3: 增强现有页面（可选）

对现有页面进行功能增强。

| 文档 | 说明 | 工作量 |
|------|------|--------|
| [Phase3-知识引用与Sandbox预览](DeerFlow原型设计-Phase3-知识引用与Sandbox预览.md) | M3 知识引用追踪 + M8 Sandbox 预览 | 2 天 |

### Phase 3 页面清单

```
📁 Phase 3
├── M3 知识引用展示
│   ├── m3/reference-analysis.html      # 引用分析页
│   ├── m3/doc-detail-references.html   # 文档详情-引用记录 Tab
│   └── m3/unreferenced-docs.html       # 未引用文档列表
│
└── M8 Sandbox 预览
    ├── m8/code-detail-sandbox.html  # 代码详情-Sandbox Tab
    ├── m8/sandbox-running.html      # Sandbox 执行中状态
    ├── m8/sandbox-complete.html     # Sandbox 执行完成状态
    ├── m8/sandbox-failed.html       # Sandbox 执行失败状态
    ├── m8/sandbox-terminal.html     # Sandbox 终端面板
    ├── components/resource-usage.html  # 资源使用组件
    └── components/log-viewer.html      # 日志查看器组件
```

---

## 可复用的现有原型

以下原型可直接复用，无需大改：

| 模块 | 页面 | 状态 |
|------|------|------|
| Portal | 登录页、工作台 | ✅ 可复用 |
| M1 | 项目列表、项目详情、成员管理 | ✅ 可复用 |
| M2 | 项目信息录入 | ✅ 可复用 |
| M5 | Bug 工单列表（状态标签调整） | ⚡ 微调 |
| M6 | 需求工单列表（状态标签调整） | ⚡ 微调 |
| M9 | 测试报告列表和详情 | ✅ 可复用 |

---

## 设计规范引用

所有原型设计遵循以下规范文档：

- [页面原型风格规范.md](页面原型风格规范.md) - 色彩、字体、组件规范
- [统一入口与单点登录-设计说明.md](统一入口与单点登录-设计说明.md) - 登录与导航规范

---

## 工作量总结

| Phase | 内容 | 工作量 |
|-------|------|--------|
| Phase 1 | 对话式入口 + HITL 卡片 | 5-8 天 |
| Phase 2 | 执行监控 + 配置页签 | 3-5 天 |
| Phase 3 | 知识引用 + Sandbox 预览 | 2 天 |
| **总计** | | **10-15 天** |

---

## 实施建议

1. **Phase 1 优先启动**：核心交互变化，影响整体用户体验
2. **Phase 2 并行开发**：可与后端 Agent 开发同步进行
3. **Phase 3 按需实施**：根据产品反馈决定是否实施

---

## 关联文档

- [DeerFlow架构重设计-运维Agent生产系统.md](DeerFlow架构重设计-运维Agent生产系统.md) - 整体架构设计
- [prototypes/README.md](prototypes/README.md) - 现有原型索引
