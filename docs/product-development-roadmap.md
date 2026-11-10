# 运维 Agent 生产系统 - 产品开发计划

## 一、功能依赖关系分析

### 1.1 模块依赖图

```mermaid
flowchart TB
    subgraph Phase0["Phase 0: 基础设施"]
        Infra[基础设施部署<br/>DeerFlow/DB/Vector]
    end

    subgraph Phase1["Phase 1: 核心框架"]
        M1[M1 项目管理]
        Gateway[Gateway 接入层]
        Auth[统一鉴权]
    end

    subgraph Phase2["Phase 2: 知识基座"]
        M2[M2 知识库前置]
        M3[M3 知识库增强]
        RAG[RAGFlow 集成]
    end

    subgraph Phase3["Phase 3: 需求入口"]
        M4[M4 需求理解与分类]
        LeadAgent[Lead Agent]
        IMIntegration[IM 集成]
    end

    subgraph Phase4["Phase 4: 方案生成"]
        M5[M5 Bug 修复 Agent]
        M6[M6 新需求设计 Agent]
    end

    subgraph Phase5["Phase 5: 人工卡点"]
        M7[M7 Review 工作台]
        Middleware[HITL Middleware]
    end

    subgraph Phase6["Phase 6: 代码执行"]
        M8[M8 代码生成 Agent]
        Sandbox[Sandbox 环境]
        Linter[语法检查]
    end

    subgraph Phase7["Phase 7: 测试闭环"]
        M9[M9 测试执行 Agent]
        TestReport[测试报告]
        CICD[CI/CD 集成]
    end

    subgraph Phase8["Phase 8: 运营优化"]
        Dashboard[运营看板]
        Analytics[数据分析]
        Optimization[效果优化]
    end

    %% 依赖关系
    Infra --> M1 & Gateway & Auth
    M1 --> M2
    Gateway & Auth --> M4
    M2 --> M3
    M3 --> RAG
    RAG --> M4
    M4 --> LeadAgent
    LeadAgent --> M5 & M6
    M5 & M6 --> M7
    M7 --> Middleware
    Middleware --> M8
    M8 --> Sandbox & Linter
    Sandbox --> M9
    M9 --> TestReport & CICD
    TestReport --> Dashboard
    CICD --> Analytics
```

### 1.2 关键依赖说明

| 模块 | 前置依赖 | 被依赖于 |
|------|----------|----------|
| **基础设施** | 无 | 所有模块 |
| **M1 项目管理** | 基础设施 | M2, M4, 所有 Agent |
| **M2 知识库前置** | M1 | M3 |
| **M3 知识库增强** | M2 | M4, M5, M6 |
| **M4 需求分类** | M1, M3, Gateway | M5, M6 |
| **M5 Bug 修复** | M4, M3 | M7 |
| **M6 新需求设计** | M4, M3 | M7 |
| **M7 Review 工作台** | M5, M6 | M8 |
| **M8 代码生成** | M7, Sandbox | M9 |
| **M9 测试执行** | M8, Sandbox | 知识反馈 |

---

## 二、开发阶段规划

### Phase 0: 基础设施搭建

```mermaid
gantt
    title Phase 0: 基础设施搭建
    dateFormat  YYYY-MM-DD
    section 基础服务
    DeerFlow 部署与配置     :p0-1, 2026-11-11, 5d
    PostgreSQL 数据库搭建   :p0-2, after p0-1, 3d
    Redis 缓存搭建          :p0-3, after p0-1, 2d
    Milvus 向量库搭建       :p0-4, after p0-2, 3d
    MinIO 对象存储搭建      :p0-5, after p0-2, 2d
    section 开发环境
    开发环境配置            :p0-6, 2026-11-11, 3d
    CI/CD 流水线搭建        :p0-7, after p0-6, 3d
```

**交付物**:
- [x] DeerFlow Gateway 运行
- [x] 数据库/缓存/向量库就绪
- [x] 开发/测试环境可用
- [x] CI/CD 流水线就绪

**验收标准**:
- `make up` 一键启动所有服务
- `make dev` 进入开发模式
- 健康检查接口返回 200

---

### Phase 1: 核心框架与项目管理

```mermaid
gantt
    title Phase 1: 核心框架与项目管理
    dateFormat  YYYY-MM-DD
    section Gateway
    Gateway 路由配置        :p1-1, 2026-11-25, 3d
    统一鉴权中间件          :p1-2, after p1-1, 4d
    项目路由选择器          :p1-3, after p1-2, 3d
    section M1 项目管理
    项目 CRUD API           :p1-4, 2026-11-25, 4d
    Agent 实例配置          :p1-5, after p1-4, 4d
    项目成员与权限          :p1-6, after p1-5, 3d
    项目管理 Web UI         :p1-7, after p1-4, 6d
```

**交付物**:
- [x] 项目创建/编辑/删除 API
- [x] Agent 实例配置功能
- [x] 项目权限管理
- [x] 项目管理 Web UI

**验收标准**:
- 可创建项目并配置 Agent 参数
- 支持多项目切换
- 项目间数据隔离

---

### Phase 2: 知识库基座

```mermaid
gantt
    title Phase 2: 知识库基座
    dateFormat  YYYY-MM-DD
    section M2 知识库前置
    项目信息录入 API        :p2-1, 2026-12-10, 4d
    知识就绪校验逻辑        :p2-2, after p2-1, 3d
    知识就绪中间件          :p2-3, after p2-2, 2d
    section M3 知识库增强
    RAGFlow 集成            :p2-4, 2026-12-10, 5d
    文档索引服务            :p2-5, after p2-4, 4d
    代码索引服务            :p2-6, after p2-5, 4d
    知识检索 Skill          :p2-7, after p2-6, 3d
    section Web UI
    知识库管理页面          :p2-8, after p2-1, 5d
    文档上传与预览          :p2-9, after p2-8, 3d
```

**交付物**:
- [x] 项目信息录入（概述、架构、配置等）
- [x] RAGFlow 集成完成
- [x] 文档/代码索引服务
- [x] `knowledge-search` Skill
- [x] 知识库管理 Web UI

**验收标准**:
- 上传文档后可被语义检索
- 代码仓库可被索引和检索
- 知识就绪校验阻止未准备项目进入流程

---

### Phase 3: 需求入口与分类

```mermaid
gantt
    title Phase 3: 需求入口与分类
    dateFormat  YYYY-MM-DD
    section Lead Agent
    Lead Agent 基础框架     :p3-1, 2026-12-25, 4d
    需求分析 Skill          :p3-2, after p3-1, 4d
    需求分类逻辑            :p3-3, after p3-2, 3d
    section M4 需求理解
    需求提交 API            :p3-4, 2026-12-25, 3d
    工单创建与管理          :p3-5, after p3-4, 3d
    需求列表 Web UI         :p3-6, after p3-5, 4d
    section IM 集成
    飞书 Bot 集成           :p3-7, after p3-3, 4d
    Slack Bot 集成          :p3-8, after p3-7, 3d
    钉钉 Bot 集成           :p3-9, after p3-8, 3d
```

**交付物**:
- [x] Lead Agent 核心框架
- [x] `demand-analysis` Skill
- [x] 需求提交 API
- [x] 工单管理系统
- [x] IM Bot 集成（飞书/Slack/钉钉）

**验收标准**:
- 通过 Web/IM 提交需求
- 自动分类为 Bug 或新需求
- 创建工单并关联项目

---

### Phase 4: 方案生成 Agents

```mermaid
gantt
    title Phase 4: 方案生成 Agents
    dateFormat  YYYY-MM-DD
    section M5 Bug 修复
    Bug Fix Agent 框架      :p4-1, 2027-01-10, 4d
    问题定位 Skill          :p4-2, after p4-1, 4d
    根因分析 Skill          :p4-3, after p4-2, 3d
    修复方案生成            :p4-4, after p4-3, 4d
    section M6 新需求设计
    Feature Agent 框架      :p4-5, 2027-01-10, 4d
    架构设计 Skill          :p4-6, after p4-5, 4d
    API 设计 Skill          :p4-7, after p4-6, 3d
    设计文档生成            :p4-8, after p4-7, 4d
    section 集成测试
    Agent 集成测试          :p4-9, after p4-4, 3d
```

**交付物**:
- [x] Bug Fix Sub-Agent
- [x] Feature Design Sub-Agent
- [x] 问题定位/根因分析 Skills
- [x] 架构设计/API 设计 Skills
- [x] 结构化方案输出

**验收标准**:
- Bug 工单自动生成修复方案
- 新需求工单自动生成设计文档
- 方案包含影响范围评估

---

### Phase 5: 人工 Review 工作台

```mermaid
gantt
    title Phase 5: 人工 Review 工作台
    dateFormat  YYYY-MM-DD
    section M7 Review
    HITL Middleware 开发    :p5-1, 2027-02-01, 5d
    Review 状态机           :p5-2, after p5-1, 3d
    审批 API                :p5-3, after p5-2, 3d
    section Web UI
    待审列表页面            :p5-4, 2027-02-01, 4d
    方案详情与对比          :p5-5, after p5-4, 4d
    通过/驳回操作           :p5-6, after p5-5, 3d
    审计日志页面            :p5-7, after p5-6, 3d
    section 通知
    Review 通知推送         :p5-8, after p5-3, 3d
    超时升级机制            :p5-9, after p5-8, 2d
```

**交付物**:
- [x] HITL Middleware
- [x] Review 状态管理
- [x] 待审列表 Web UI
- [x] 通过/驳回/评论功能
- [x] 审计日志
- [x] 通知与超时升级

**验收标准**:
- 方案生成后进入待审状态
- 支持多级 Review（方案→代码）
- 驳回后自动回退重新生成
- 所有操作有审计记录

---

### Phase 6: 代码生成与执行

```mermaid
gantt
    title Phase 6: 代码生成与执行
    dateFormat  YYYY-MM-DD
    section Sandbox
    Docker Sandbox 配置     :p6-1, 2027-02-20, 4d
    Sandbox 资源管理        :p6-2, after p6-1, 3d
    网络隔离策略            :p6-3, after p6-2, 3d
    section M8 代码生成
    Code Gen Agent 框架     :p6-4, 2027-02-20, 4d
    代码生成 Skill          :p6-5, after p6-4, 5d
    语法检查 Skill          :p6-6, after p6-5, 3d
    代码格式化              :p6-7, after p6-6, 2d
    section 集成
    Git 集成（MR 创建）     :p6-8, after p6-7, 4d
    代码 Review 触发        :p6-9, after p6-8, 2d
```

**交付物**:
- [x] Docker AIO Sandbox
- [x] Code Generation Sub-Agent
- [x] `code-generation` Skill
- [x] `linter-check` Skill
- [x] Git MR 自动创建

**验收标准**:
- 在隔离 Sandbox 中生成代码
- 自动语法检查并修复
- 生成代码 diff 预览
- 自动创建 Git MR

---

### Phase 7: 测试执行与闭环

```mermaid
gantt
    title Phase 7: 测试执行与闭环
    dateFormat  YYYY-MM-DD
    section M9 测试执行
    Test Agent 框架         :p7-1, 2027-03-10, 4d
    测试用例生成 Skill      :p7-2, after p7-1, 5d
    测试执行引擎            :p7-3, after p7-2, 4d
    测试报告生成            :p7-4, after p7-3, 3d
    section CI/CD 集成
    CI 流水线触发           :p7-5, after p7-4, 3d
    测试状态同步            :p7-6, after p7-5, 2d
    section 知识反馈
    知识库反馈写入          :p7-7, after p7-6, 3d
    案例库沉淀              :p7-8, after p7-7, 3d
```

**交付物**:
- [x] Test Execution Sub-Agent
- [x] `test-generation` Skill
- [x] `test-execution` Skill
- [x] 测试报告生成
- [x] CI/CD 集成
- [x] 知识反馈写入

**验收标准**:
- 自动生成测试用例
- 在 Sandbox 中执行测试
- 生成测试报告（通过率、覆盖率）
- 完成后自动沉淀知识

---

### Phase 8: 运营优化

```mermaid
gantt
    title Phase 8: 运营优化
    dateFormat  YYYY-MM-DD
    section 运营看板
    任务统计看板            :p8-1, 2027-04-01, 4d
    效率分析报表            :p8-2, after p8-1, 4d
    质量趋势分析            :p8-3, after p8-2, 3d
    section 优化迭代
    Agent 效果评估          :p8-4, after p8-3, 5d
    Prompt 优化             :p8-5, after p8-4, 5d
    模型微调评估            :p8-6, after p8-5, 5d
    section 扩展功能
    多模型支持              :p8-7, 2027-04-01, 5d
    自定义 Skill 平台       :p8-8, after p8-7, 7d
```

**交付物**:
- [x] 运营数据看板
- [x] 效率/质量分析报表
- [x] Agent 效果评估体系
- [x] 多模型支持
- [x] 自定义 Skill 平台

**验收标准**:
- 可视化任务处理统计
- 可追踪效率提升数据
- 支持切换不同 LLM 模型

---

## 三、里程碑总览

```mermaid
timeline
    title 产品开发里程碑
    
    section 2026 Q4
        11月 : Phase 0 基础设施
             : Phase 1 核心框架
        12月 : Phase 2 知识库
             : Phase 3 需求入口
    
    section 2027 Q1
        1月 : Phase 4 方案生成
        2月 : Phase 5 Review 工作台
           : Phase 6 代码生成
        3月 : Phase 7 测试闭环
    
    section 2027 Q2
        4月 : Phase 8 运营优化
        5月 : 正式发布 v1.0
```

### 里程碑定义

| 里程碑 | 目标日期 | 关键交付 | 验收标准 |
|--------|----------|----------|----------|
| **M0: 环境就绪** | 2026-11-24 | 基础设施部署完成 | 所有服务健康运行 |
| **M1: 框架可用** | 2026-12-09 | 项目管理 + Gateway | 可创建项目并配置 |
| **M2: 知识就绪** | 2026-12-24 | 知识库完整功能 | 文档/代码可检索 |
| **M3: 需求可入** | 2027-01-09 | Lead Agent + 分类 | 需求自动分类 |
| **M4: 方案可出** | 2027-01-31 | Bug/Feature Agent | 自动生成方案 |
| **M5: 流程闭环** | 2027-02-28 | Review + 代码生成 | 端到端流程可用 |
| **M6: MVP 完成** | 2027-03-31 | 测试执行 + 知识反馈 | 完整闭环可用 |
| **M7: GA 发布** | 2027-05-15 | 运营优化 + 稳定性 | 生产环境就绪 |

---

## 四、资源需求估算

### 4.1 团队配置建议

| 角色 | 人数 | 主要职责 |
|------|------|----------|
| **Tech Lead** | 1 | 架构设计、技术决策、代码审查 |
| **后端开发** | 2-3 | Agent 开发、API、Middleware |
| **前端开发** | 1-2 | Web UI、工作台 |
| **AI/ML 工程师** | 1 | Skill 开发、Prompt 优化、RAG 调优 |
| **DevOps** | 1 | 基础设施、CI/CD、监控 |
| **QA** | 1 | 测试、质量保障 |
| **PM** | 1 | 产品管理、需求协调 |

### 4.2 基础设施资源

| 资源 | 开发环境 | 生产环境 |
|------|----------|----------|
| **计算** | 8C16G * 2 | 16C32G * 3 (Gateway) |
| **数据库** | PostgreSQL 单节点 | PostgreSQL HA |
| **向量库** | Milvus 单节点 | Milvus 集群 |
| **缓存** | Redis 单节点 | Redis Cluster |
| **存储** | 100GB | 1TB+ |
| **LLM API** | 测试额度 | 生产额度 |

---

## 五、风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| DeerFlow 框架限制 | 功能受限 | 中 | 提前评估，必要时 fork 定制 |
| LLM 效果不稳定 | 方案质量波动 | 高 | 多模型备选，人工 Review 兜底 |
| RAG 检索精度低 | 上下文不准确 | 中 | 调优 embedding，混合检索 |
| Sandbox 安全风险 | 代码逃逸 | 低 | 严格网络隔离，资源限制 |
| 人工 Review 瓶颈 | 流程堵塞 | 中 | 超时升级，批量审批 |

---

## 六、成功指标

### 6.1 效率指标

| 指标 | 基线 | 目标 |
|------|------|------|
| Bug 修复时间 | 4h（人工） | 1h（含 Review） |
| 需求设计时间 | 8h（人工） | 2h（含 Review） |
| 代码编写时间 | 2h（人工） | 30min |
| 测试覆盖率 | 60% | 80%+ |

### 6.2 质量指标

| 指标 | 目标 |
|------|------|
| 方案一次通过率 | > 70% |
| 代码语法检查通过率 | > 95% |
| 测试一次通过率 | > 80% |
| 生产缺陷率 | < 5% |

### 6.3 运营指标

| 指标 | 目标 |
|------|------|
| 日活跃项目数 | > 10 |
| 月处理任务数 | > 500 |
| 用户满意度 | > 4.0/5.0 |
