---
name: test-execution
description: 执行测试并验证代码变更。包括单元测试、集成测试、回归测试和测试报告生成。
---

# 测试执行技能 (Test Execution Skill)

## 概述

此技能负责执行各类测试，验证代码变更的正确性和完整性，生成详细的测试报告，支持 CI/CD 流程。

## 适用场景

- 代码变更后的验证测试
- PR 合并前的检查
- 发布前的回归测试
- 定期的健康检查

## 测试流程

### 第一阶段：测试准备

1. **环境检查**
   - 验证测试环境可用
   - 检查依赖服务状态
   - 准备测试数据

2. **测试范围确定**
   - 根据变更确定测试范围
   - 选择测试套件
   - 设置测试参数

3. **配置测试环境**
   ```yaml
   test_environment:
     database: test_db
     redis: test_redis
     external_services: mock
   ```

### 第二阶段：测试执行

1. **单元测试**
   ```bash
   # Python 项目
   pytest tests/unit/ -v --cov=src --cov-report=html
   
   # Node.js 项目
   npm run test:unit -- --coverage
   ```

2. **集成测试**
   ```bash
   # 启动测试服务
   pytest tests/integration/ -v --tb=short
   ```

3. **端到端测试**（如适用）
   ```bash
   # E2E 测试
   pytest tests/e2e/ -v
   ```

### 第三阶段：结果分析

1. **测试结果汇总**
   - 通过/失败/跳过统计
   - 执行时间分析
   - 覆盖率报告

2. **失败分析**
   - 失败用例分类
   - 错误原因识别
   - 修复建议

3. **回归分析**
   - 与历史结果对比
   - 性能变化趋势
   - 新引入问题识别

## 输出格式

```json
{
  "test_run_id": "TEST-2024-001",
  "source": {
    "type": "code_generation|pr|manual",
    "id": "GEN-2024-001"
  },
  "summary": {
    "total": 150,
    "passed": 145,
    "failed": 3,
    "skipped": 2,
    "duration": "45.3s",
    "coverage": {
      "lines": 85.2,
      "branches": 78.5,
      "functions": 90.1
    }
  },
  "test_suites": [
    {
      "name": "单元测试",
      "type": "unit",
      "total": 100,
      "passed": 98,
      "failed": 1,
      "skipped": 1,
      "duration": "15.2s"
    },
    {
      "name": "集成测试",
      "type": "integration",
      "total": 50,
      "passed": 47,
      "failed": 2,
      "skipped": 1,
      "duration": "30.1s"
    }
  ],
  "failures": [
    {
      "test_name": "test_user_login",
      "suite": "integration",
      "error": "AssertionError: expected 200, got 401",
      "traceback": "错误堆栈",
      "analysis": "可能原因分析",
      "suggestion": "修复建议"
    }
  ],
  "coverage_report": {
    "uncovered_files": ["文件列表"],
    "critical_uncovered": ["关键未覆盖代码"]
  },
  "quality_gates": {
    "min_coverage_met": true,
    "no_critical_failures": false,
    "performance_acceptable": true
  },
  "recommendation": {
    "status": "pass|fail|needs_review",
    "message": "测试结论",
    "next_action": "建议下一步"
  }
}
```

## 质量门禁

```yaml
quality_gates:
  coverage:
    lines: 80      # 最低行覆盖率
    branches: 70   # 最低分支覆盖率
  
  failures:
    unit: 0        # 单元测试不允许失败
    integration: 0 # 集成测试不允许失败
  
  performance:
    max_duration: 300  # 最大执行时间（秒）
    regression_threshold: 10  # 性能回归阈值（%）
```

## CI/CD 集成

### GitHub Actions 集成

```yaml
# 触发测试的场景
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

# 测试步骤
jobs:
  test:
    steps:
      - name: Run Tests
        run: |
          pytest --junitxml=report.xml
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: report.xml
```

### 测试报告发布

- 生成 JUnit XML 格式报告
- 发布到 PR 评论
- 更新测试徽章

## 测试数据管理

1. **固定测试数据**
   - 版本化管理
   - 环境隔离
   - 定期更新

2. **动态测试数据**
   - 工厂模式生成
   - 使用 Faker 库
   - 测试后清理

3. **敏感数据处理**
   - 使用脱敏数据
   - 环境变量注入
   - 安全存储

## 失败处理

### 自动重试策略

```python
# 针对不稳定测试的重试配置
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_external_api():
    pass
```

### 失败通知

- 测试失败时通知相关人员
- 提供失败详情和日志链接
- 建议修复方向

## 与其他技能的协作

- 从 `code-generation` 接收待测试代码
- 测试通过后更新需求状态
- 测试失败时通知 HITL 审核
- 测试结果同步到知识库
