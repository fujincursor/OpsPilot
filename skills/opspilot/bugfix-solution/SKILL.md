---
name: bugfix-solution
description: 针对 Bug 类型需求生成修复方案。包括根因分析、修复策略、代码变更建议和测试计划。
---

# Bug 修复方案技能 (BugFix Solution Skill)

## 概述

此技能专注于 Bug 类型需求的解决方案生成，提供从根因分析到修复验证的完整流程。

## 适用场景

- 需求分析确认为 Bug 类型
- 系统运行异常需要快速定位
- 历史 Bug 复现需要分析
- 紧急故障需要快速响应

## 修复流程

### 第一阶段：问题定位

1. **信息收集**
   - 获取错误日志和堆栈信息
   - 收集复现步骤和环境信息
   - 了解问题发生的时间线

2. **根因分析**
   ```
   使用 5 Whys 方法：
   - Why 1: 为什么出现这个错误？
   - Why 2: 为什么会触发这个条件？
   - Why 3: 为什么这个检查没有生效？
   - Why 4: 为什么测试没有覆盖？
   - Why 5: 根本原因是什么？
   ```

3. **影响范围确认**
   - 确认受影响的功能模块
   - 评估数据影响（是否有数据损坏）
   - 识别相关联的系统

### 第二阶段：方案设计

1. **修复策略选择**

   | 策略类型 | 适用场景 | 风险等级 |
   |---------|---------|---------|
   | 热修复 (Hotfix) | 线上紧急问题 | 高 |
   | 常规修复 | 非紧急 Bug | 中 |
   | 重构修复 | 设计缺陷 | 低 |
   | 临时绕过 | 无法立即修复 | 视情况 |

2. **代码变更方案**
   - 明确需要修改的文件列表
   - 设计最小化变更方案
   - 考虑向后兼容性

3. **回滚方案**
   - 准备回滚脚本或步骤
   - 确认数据恢复方案
   - 设定回滚触发条件

### 第三阶段：测试计划

1. **单元测试**
   - 针对修复代码编写测试用例
   - 覆盖边界条件
   - 验证修复有效性

2. **集成测试**
   - 验证与相关模块的交互
   - 确认不影响现有功能
   - 回归测试关键路径

3. **验收标准**
   - 原问题不再复现
   - 不引入新的问题
   - 性能无明显下降

## 输出格式

```json
{
  "solution_id": "SOL-2024-001",
  "requirement_id": "REQ-2024-001",
  "type": "bugfix",
  "analysis": {
    "root_cause": "根因描述",
    "impact_assessment": "影响评估",
    "affected_modules": ["受影响模块"]
  },
  "solution": {
    "strategy": "hotfix|regular|refactor|workaround",
    "description": "修复方案描述",
    "changes": [
      {
        "file": "文件路径",
        "type": "modify|add|delete",
        "description": "变更描述",
        "code_snippet": "代码片段（如适用）"
      }
    ],
    "rollback_plan": "回滚方案"
  },
  "testing": {
    "unit_tests": ["单元测试列表"],
    "integration_tests": ["集成测试列表"],
    "acceptance_criteria": ["验收标准"]
  },
  "deployment": {
    "environment": "target_environment",
    "steps": ["部署步骤"],
    "verification": ["验证步骤"]
  },
  "risk_assessment": {
    "level": "low|medium|high",
    "factors": ["风险因素"],
    "mitigations": ["缓解措施"]
  }
}
```

## 紧急 Bug 处理流程

对于 P0/P1 级别的紧急 Bug：

1. **立即响应**（5分钟内）
   - 确认问题现象
   - 评估是否需要紧急止血

2. **快速止血**（30分钟内）
   - 如必要，执行临时缓解措施
   - 通知相关干系人

3. **根因修复**（视复杂度）
   - 完成根因分析
   - 实施永久修复

4. **事后复盘**
   - 记录事件时间线
   - 分析改进措施
   - 更新知识库

## 与其他技能的协作

- 从 `requirement-analysis` 接收 Bug 需求
- 将修复方案传递给 `code-generation` 实施
- 生成测试计划交给 `test-execution` 验证
- 更新相关知识到 `knowledge-retrieval` 知识库
