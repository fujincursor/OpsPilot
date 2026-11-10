# Phase 1: 对话式需求入口 · HTML 原型

本目录包含 DeerFlow 架构下**对话式需求入口**和 **HITL 审批卡片**的 HTML 原型。

## 页面清单

| 页面 | 文件 | 说明 |
|------|------|------|
| 对话主页面 | [index.html](index.html) | 带消息流的对话界面 |
| 新会话欢迎 | [welcome.html](welcome.html) | 新建会话的欢迎状态 |
| HITL 审批 | [approval.html](approval.html) | 内嵌审批卡片示例 |

## 核心组件

### 1. 对话布局
- 侧栏：项目选择器 + 历史会话列表
- 主区域：消息流 + 输入区域

### 2. 消息类型
- 用户消息（右对齐蓝底）
- Agent 消息（左对齐白底）
- 知识检索卡片
- 分类结果卡片
- Sub-Agent 执行进度卡片

### 3. HITL 审批卡片
- 待审批状态（橙色边框）
- 已通过状态（绿色边框）
- 已驳回状态（红色边框）
- 超时提醒组件

## 设计规范

遵循 [页面原型风格规范](../../页面原型风格规范.md)

## 相关文档

- [DeerFlow原型设计-Phase1-对话式需求入口.md](../../DeerFlow原型设计-Phase1-对话式需求入口.md)
- [DeerFlow原型设计-Phase1-HITL审批卡片.md](../../DeerFlow原型设计-Phase1-HITL审批卡片.md)
