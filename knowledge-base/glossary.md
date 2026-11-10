# 术语表

本文档收录 OpsPilot 中使用的专业术语和概念。

---

## A

### Agent
**智能代理**。在 OpsPilot 中，Agent 是执行特定任务的 AI 实体。系统采用 Lead Agent + Sub-Agents 架构。

### API (Application Programming Interface)
**应用程序编程接口**。OpsPilot 提供 RESTful API 供外部系统调用。

### Analysis
**分析**。AI 对需求进行的理解和拆解过程，识别需求类型、影响范围、优先级等。

---

## B

### Bug
**软件缺陷**。软件中的错误或问题，需要修复。

### Bugfix
**Bug 修复**。针对 Bug 的修复方案和代码变更。

---

## C

### Code Generation
**代码生成**。AI 根据方案自动生成代码的过程。

### Coverage
**覆盖率**。测试覆盖代码的比例，包括行覆盖率、分支覆盖率等。

### CI/CD (Continuous Integration/Continuous Deployment)
**持续集成/持续部署**。自动化的构建、测试和部署流程。

---

## D

### DeerFlow
**DeerFlow 框架**。OpsPilot 采用的 AI Agent 框架，提供 Agent 调度、Skill 管理、Sandbox 执行等功能。

### Diff
**差异对比**。代码变更前后的对比视图。

---

## E

### Embedding
**嵌入向量**。将文本转换为数值向量的过程，用于知识检索和语义搜索。

---

## F

### Feature
**功能特性**。软件的新增功能需求。

### Feature Design
**功能设计**。新功能的技术设计方案。

---

## G

### Gate
**门禁**。质量检查点，如测试必须通过才能继续。

---

## H

### HITL (Human-in-the-Loop)
**人类在回路**。在 AI 自动化流程中引入人工审核环节，确保结果准确性和风险可控。

---

## I

### Integration
**集成**。与外部系统（如 Jira、GitHub）的连接和数据同步。

---

## K

### Knowledge Base
**知识库**。存储项目相关文档的系统，用于 AI 检索和理解上下文。

---

## L

### Lead Agent
**主导代理**。负责任务调度和协调 Sub-Agent 工作的主 Agent。

### LLM (Large Language Model)
**大语言模型**。如 GPT-4、Claude 等，是 AI 能力的核心。

---

## M

### Memory
**记忆系统**。Agent 保持上下文和历史信息的机制。

### Mock
**模拟**。用模拟数据或服务替代真实服务的测试技术。

---

## P

### PR (Pull Request)
**拉取请求**。代码合并请求，通常需要代码审查。

### Priority
**优先级**。需求或任务的紧急程度，如 P0（最高）到 P3（最低）。

---

## Q

### Quality Gate
**质量门禁**。代码或方案必须满足的质量标准。

---

## R

### RAG (Retrieval-Augmented Generation)
**检索增强生成**。结合知识检索和生成模型的技术，提高 AI 回答的准确性。

### Requirement
**需求**。待处理的任务，可以是 Bug、Feature 或其他任务类型。

### Review
**审核**。对 AI 生成方案的人工审查过程。

### Root Cause
**根本原因**。导致问题的根本原因，而非表面症状。

---

## S

### Sandbox
**沙箱**。隔离的安全执行环境，用于运行代码和测试。

### Severity
**严重程度**。Bug 或问题的严重级别。

### Skill
**技能**。定义 Agent 能力的模块，包含提示词和逻辑流程。

### Solution
**解决方案**。针对需求生成的修复或设计方案。

### Sub-Agent
**子代理**。执行特定子任务的 Agent，如 Researcher、Coder、Reporter。

---

## T

### Test
**测试**。验证代码正确性的自动化检查。

### Thread
**会话线程**。与 AI 的对话上下文，保持对话连续性。

### Token
**令牌**。
1. 认证令牌：用于 API 身份验证
2. AI 令牌：LLM 处理的文本单位

---

## U

### Unit Test
**单元测试**。测试单个函数或组件的测试。

---

## V

### Vector
**向量**。文本的数值表示，用于语义搜索。

---

## W

### Workflow
**工作流**。定义任务处理流程的配置，如分析→方案→审核→代码→测试。

### Webhook
**网络钩子**。事件触发的 HTTP 回调通知。

---

## 缩写对照表

| 缩写 | 全称 | 中文 |
|------|------|------|
| AI | Artificial Intelligence | 人工智能 |
| API | Application Programming Interface | 应用程序接口 |
| CI | Continuous Integration | 持续集成 |
| CD | Continuous Deployment | 持续部署 |
| CLI | Command Line Interface | 命令行接口 |
| DB | Database | 数据库 |
| HITL | Human-in-the-Loop | 人类在回路 |
| IDE | Integrated Development Environment | 集成开发环境 |
| JWT | JSON Web Token | JSON 网络令牌 |
| LLM | Large Language Model | 大语言模型 |
| MCP | Model Context Protocol | 模型上下文协议 |
| PR | Pull Request | 拉取请求 |
| RAG | Retrieval-Augmented Generation | 检索增强生成 |
| SDK | Software Development Kit | 软件开发工具包 |
| SSE | Server-Sent Events | 服务器推送事件 |
| URL | Uniform Resource Locator | 统一资源定位符 |
| WS | WebSocket | 网络套接字 |

---

*文档版本: 1.0*
*最后更新: 2024*
