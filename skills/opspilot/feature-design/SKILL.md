---
name: feature-design
description: 针对功能请求生成设计方案。包括需求拆解、技术方案、接口设计和实施计划。
---

# 功能设计技能 (Feature Design Skill)

## 概述

此技能专注于 Feature 和 Enhancement 类型需求的方案设计，提供从需求理解到技术实现的完整设计流程。

## 适用场景

- 新功能需求设计
- 现有功能增强
- 系统架构优化
- 技术债务偿还

## 设计流程

### 第一阶段：需求理解

1. **用户故事分析**
   ```
   作为 [用户角色]
   我希望 [功能描述]
   以便 [业务价值]
   ```

2. **功能拆解**
   - 核心功能（Must Have）
   - 重要功能（Should Have）
   - 可选功能（Could Have）
   - 暂不考虑（Won't Have）

3. **边界定义**
   - 明确功能范围
   - 识别非功能需求
   - 确定约束条件

### 第二阶段：技术方案

1. **架构设计**
   - 模块划分
   - 组件交互
   - 数据流设计

2. **接口设计**
   ```yaml
   API 设计原则：
   - RESTful 风格
   - 版本控制
   - 错误处理
   - 认证授权
   ```

3. **数据模型**
   - 实体定义
   - 关系映射
   - 索引设计

4. **技术选型**
   - 框架/库选择
   - 依赖管理
   - 兼容性考虑

### 第三阶段：实施计划

1. **任务分解**
   - 开发任务拆分
   - 依赖关系标注
   - 工作量估算

2. **里程碑规划**
   - 阶段性目标
   - 交付物定义
   - 验收标准

3. **风险识别**
   - 技术风险
   - 资源风险
   - 时间风险

## 输出格式

```json
{
  "design_id": "DES-2024-001",
  "requirement_id": "REQ-2024-001",
  "type": "feature|enhancement",
  "overview": {
    "title": "功能标题",
    "description": "功能描述",
    "user_story": "用户故事",
    "business_value": "业务价值"
  },
  "scope": {
    "in_scope": ["范围内功能"],
    "out_of_scope": ["范围外功能"],
    "dependencies": ["依赖项"],
    "constraints": ["约束条件"]
  },
  "technical_design": {
    "architecture": {
      "diagram": "架构图描述或链接",
      "components": [
        {
          "name": "组件名",
          "responsibility": "职责",
          "technology": "技术栈"
        }
      ],
      "data_flow": "数据流描述"
    },
    "api_design": [
      {
        "method": "GET|POST|PUT|DELETE",
        "endpoint": "/api/v1/resource",
        "description": "接口描述",
        "request": "请求格式",
        "response": "响应格式"
      }
    ],
    "data_model": {
      "entities": ["实体列表"],
      "relationships": ["关系描述"],
      "migrations": ["数据迁移"]
    }
  },
  "implementation_plan": {
    "phases": [
      {
        "name": "阶段名",
        "tasks": ["任务列表"],
        "deliverables": ["交付物"],
        "duration": "预估时间"
      }
    ],
    "milestones": [
      {
        "name": "里程碑",
        "criteria": "完成标准",
        "date": "目标日期"
      }
    ]
  },
  "testing_strategy": {
    "unit_testing": "单元测试策略",
    "integration_testing": "集成测试策略",
    "acceptance_testing": "验收测试策略"
  },
  "risk_assessment": {
    "risks": [
      {
        "description": "风险描述",
        "probability": "low|medium|high",
        "impact": "low|medium|high",
        "mitigation": "缓解措施"
      }
    ]
  },
  "review_required": true,
  "estimated_effort": "工作量估算"
}
```

## 设计原则

1. **简单性**
   - 优先选择简单方案
   - 避免过度设计
   - 迭代优化

2. **可扩展性**
   - 预留扩展点
   - 松耦合设计
   - 配置化优先

3. **可维护性**
   - 清晰的代码结构
   - 完善的文档
   - 易于调试

4. **安全性**
   - 输入验证
   - 权限控制
   - 数据保护

## 与其他技能的协作

- 从 `requirement-analysis` 接收 Feature 需求
- 设计方案需要人工审核后执行
- 审核通过后交给 `code-generation` 实施
- 实施完成后由 `test-execution` 验证
