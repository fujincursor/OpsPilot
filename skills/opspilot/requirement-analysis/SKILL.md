---
name: requirement-analysis
description: 分析运维需求，进行分类和优先级评估。用于处理 Bug 报告、功能请求、运维工单等需求的智能分析。
---

# 需求分析技能 (Requirement Analysis Skill)

## 概述

此技能提供系统化的运维需求分析方法，支持从多种来源（GitHub Issues、Jira 工单、用户反馈、告警系统）识别、分类和优先级排序需求。

## 适用场景

- 接收到新的 Bug 报告或 Issue
- 收到功能请求或改进建议
- 运维告警需要分析和处理
- 用户反馈需要转化为可执行任务

## 分析方法论

### 第一阶段：需求识别

1. **来源分析**
   - 识别需求来源（Issue、告警、用户反馈）
   - 提取关键信息（标题、描述、标签、优先级）
   - 收集上下文（相关日志、截图、环境信息）

2. **初步分类**
   - Bug（缺陷）：功能不符合预期
   - Feature（功能）：新功能请求
   - Enhancement（增强）：现有功能改进
   - Maintenance（维护）：日常运维任务
   - Security（安全）：安全相关问题

### 第二阶段：深度分析

1. **影响评估**
   - 影响范围（单用户/部分用户/全部用户）
   - 业务影响（关键业务/一般业务/非核心）
   - 技术影响（系统稳定性/性能/数据完整性）

2. **紧急程度判定**
   - P0 - 紧急：系统不可用，需立即处理
   - P1 - 高：核心功能受影响，24小时内处理
   - P2 - 中：功能受限，本周内处理
   - P3 - 低：优化建议，计划处理

3. **复杂度评估**
   - 技术复杂度（简单修复/中等改动/重构）
   - 依赖关系（独立/有依赖/跨系统）
   - 测试范围（单元测试/集成测试/全量回归）

### 第三阶段：知识库关联

1. **历史问题检索**
   - 搜索相似历史 Issue
   - 检查是否有已知解决方案
   - 关联相关文档和知识库

2. **代码关联**
   - 定位可能涉及的代码模块
   - 识别相关配置文件
   - 标记潜在影响范围

## 输出格式

分析完成后，输出结构化的需求分析报告：

```json
{
  "requirement_id": "REQ-2024-001",
  "title": "需求标题",
  "type": "bug|feature|enhancement|maintenance|security",
  "priority": "P0|P1|P2|P3",
  "source": {
    "type": "github_issue|jira|alert|feedback",
    "id": "原始来源ID",
    "url": "来源链接"
  },
  "analysis": {
    "summary": "问题概述",
    "root_cause": "根因分析（如适用）",
    "impact": {
      "scope": "影响范围",
      "severity": "严重程度",
      "affected_users": "受影响用户"
    },
    "complexity": {
      "level": "low|medium|high",
      "estimated_effort": "预估工作量",
      "dependencies": ["依赖项列表"]
    }
  },
  "related": {
    "similar_issues": ["相似问题列表"],
    "knowledge_base": ["相关知识库文章"],
    "code_modules": ["相关代码模块"]
  },
  "recommendation": {
    "action": "建议处理方式",
    "assignee_type": "bugfix_agent|feature_agent|manual",
    "next_steps": ["下一步操作"]
  }
}
```

## 与其他技能的协作

- 分析完成后，根据需求类型推荐后续处理技能
- Bug 类型 → `bugfix-solution` 技能
- Feature 类型 → `feature-design` 技能
- 需要代码修改 → `code-generation` 技能
- 需要测试验证 → `test-execution` 技能

## 质量检查

在完成分析前，确认：
- [ ] 需求描述清晰完整
- [ ] 分类和优先级合理
- [ ] 已检索相关历史记录
- [ ] 已关联相关知识库
- [ ] 下一步行动明确
