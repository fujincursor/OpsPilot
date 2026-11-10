---
name: code-generation
description: 根据设计方案生成代码。包括代码实现、单元测试、文档生成和代码审查准备。
---

# 代码生成技能 (Code Generation Skill)

## 概述

此技能根据 Bug 修复方案或功能设计方案，自动生成符合规范的代码实现，包括业务代码、测试代码和相关文档。

## 适用场景

- Bug 修复方案已确认
- 功能设计方案已审批
- 代码重构任务
- 自动化脚本生成

## 代码生成流程

### 第一阶段：准备工作

1. **上下文获取**
   - 读取相关设计方案
   - 分析现有代码结构
   - 理解项目编码规范

2. **依赖分析**
   - 识别需要的库/包
   - 检查版本兼容性
   - 确认安装方式

3. **环境准备**
   - 创建工作分支
   - 设置开发环境
   - 准备测试数据

### 第二阶段：代码实现

1. **代码结构规划**
   ```
   遵循项目结构：
   ├── src/
   │   ├── api/          # API 接口
   │   ├── services/     # 业务逻辑
   │   ├── models/       # 数据模型
   │   └── utils/        # 工具函数
   └── tests/
       ├── unit/         # 单元测试
       └── integration/  # 集成测试
   ```

2. **编码规范**
   - 遵循项目代码风格
   - 使用类型注解
   - 添加必要注释
   - 处理异常情况

3. **代码质量检查**
   - 静态代码分析
   - 类型检查
   - 安全扫描

### 第三阶段：测试生成

1. **单元测试**
   ```python
   # 测试用例结构
   def test_function_name():
       # Arrange - 准备测试数据
       # Act - 执行被测函数
       # Assert - 验证结果
   ```

2. **测试覆盖**
   - 正常流程测试
   - 边界条件测试
   - 异常情况测试
   - 性能基准测试（如需要）

### 第四阶段：文档生成

1. **代码文档**
   - 函数/类文档字符串
   - API 文档
   - 使用示例

2. **变更文档**
   - 变更说明
   - 升级指南（如有破坏性变更）

## 输出格式

```json
{
  "generation_id": "GEN-2024-001",
  "source": {
    "type": "solution|design",
    "id": "SOL-2024-001"
  },
  "code_changes": [
    {
      "file": "文件路径",
      "action": "create|modify|delete",
      "language": "python|typescript|yaml",
      "content": "代码内容",
      "diff": "差异对比（如为修改）"
    }
  ],
  "tests": [
    {
      "file": "测试文件路径",
      "type": "unit|integration",
      "test_cases": ["测试用例列表"]
    }
  ],
  "documentation": {
    "api_docs": "API 文档内容",
    "changelog": "变更日志条目"
  },
  "quality_checks": {
    "lint_passed": true,
    "type_check_passed": true,
    "security_scan_passed": true,
    "test_coverage": "覆盖率百分比"
  },
  "review_checklist": [
    "代码符合项目规范",
    "测试覆盖充分",
    "文档完整",
    "无安全问题"
  ]
}
```

## 代码生成原则

### 安全性原则

```
✅ 允许的操作：
- 创建/修改应用代码
- 生成配置文件
- 编写测试代码
- 更新文档

❌ 禁止的操作：
- 删除生产数据
- 修改系统权限
- 执行未审核的部署
- 访问敏感凭证
```

### 质量原则

1. **可读性**
   - 有意义的命名
   - 清晰的结构
   - 适当的注释

2. **可测试性**
   - 单一职责
   - 依赖注入
   - 可模拟外部依赖

3. **可维护性**
   - DRY 原则
   - 配置外部化
   - 日志记录

## Sandbox 执行

代码生成和执行在隔离的 Sandbox 环境中进行：

```yaml
sandbox_config:
  timeout: 300  # 执行超时（秒）
  memory_limit: 512M  # 内存限制
  network: restricted  # 网络限制
  allowed_commands:
    - python
    - pytest
    - npm
    - node
```

## 代码审查准备

生成的代码在提交前需要准备：

1. **Diff 预览**
   - 所有文件变更清单
   - 行级差异对比
   - 影响范围说明

2. **审查要点**
   - 关键逻辑变更
   - 潜在风险点
   - 需要关注的测试

3. **回滚准备**
   - 变更可逆性说明
   - 回滚步骤

## 与其他技能的协作

- 从 `bugfix-solution` 或 `feature-design` 接收方案
- 生成的代码需要人工审核
- 审核通过后交给 `test-execution` 执行测试
- 测试通过后可提交 PR
