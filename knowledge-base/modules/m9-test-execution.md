# M9: 测试用例生成与执行模块

## 1. 模块概述

测试用例生成与执行模块负责自动生成测试用例、执行测试并生成测试报告，确保代码变更的质量。

### 1.1 核心功能

- 测试用例自动生成
- 测试执行管理
- 覆盖率分析
- 测试报告生成
- CI/CD 集成

### 1.2 模块定位

```
代码变更 → 测试生成与执行 → 测试报告
                │
                ├─ 用例生成 → 基于代码生成测试
                │
                ├─ 测试执行 → Sandbox 运行测试
                │
                ├─ 覆盖率分析 → 代码覆盖统计
                │
                └─ 报告生成 → 测试结果报告
```

## 2. 测试 Agent

### 2.1 Agent 配置

```yaml
name: test_agent
display_name: 测试 Agent
description: 执行测试并验证代码变更
skills:
  - test-execution
settings:
  model: gpt-4o
  temperature: 0.2
  max_iterations: 5
```

### 2.2 test-execution Skill

Skill 核心内容：

```markdown
# test-execution Skill

## 测试流程

### 第一阶段：测试准备
1. 环境检查
2. 测试范围确定
3. 测试数据准备

### 第二阶段：测试执行
1. 单元测试
2. 集成测试
3. 覆盖率收集

### 第三阶段：结果分析
1. 测试结果汇总
2. 失败分析
3. 报告生成
```

## 3. 测试用例生成

### 3.1 生成策略

```python
class TestGenerationStrategy:
    """测试生成策略"""
    
    def generate_for_function(self, func: Function) -> List[TestCase]:
        tests = []
        
        # 1. 正常流程测试
        tests.append(self.generate_happy_path(func))
        
        # 2. 边界值测试
        tests.extend(self.generate_boundary_tests(func))
        
        # 3. 异常测试
        tests.extend(self.generate_exception_tests(func))
        
        # 4. 空值测试
        tests.extend(self.generate_null_tests(func))
        
        return tests
```

### 3.2 测试类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **Happy Path** | 正常流程 | 有效输入返回预期结果 |
| **Boundary** | 边界值 | 最大值、最小值、空值 |
| **Exception** | 异常情况 | 无效输入抛出异常 |
| **Integration** | 集成测试 | 多组件协作 |
| **Performance** | 性能测试 | 响应时间、吞吐量 |

### 3.3 生成 API

```http
POST /api/v1/tests/generate
Content-Type: application/json

{
  "code_generation_id": "gen_123",
  "test_types": ["unit", "integration"],
  "coverage_target": 80
}
```

响应：
```json
{
  "test_generation_id": "testgen_456",
  "status": "completed",
  "tests": [
    {
      "file": "tests/test_export_service.py",
      "test_count": 8,
      "test_cases": [
        "test_export_users_csv_success",
        "test_export_users_xlsx_success",
        "test_export_users_empty_fields",
        "test_export_users_invalid_format"
      ]
    }
  ]
}
```

## 4. 测试数据模型

### 4.1 测试运行

```python
class TestRun:
    id: str                      # 运行 ID
    code_generation_id: str      # 关联的代码生成
    status: TestRunStatus        # 运行状态
    started_at: datetime         # 开始时间
    completed_at: datetime       # 完成时间
    duration_ms: int             # 执行时长
    summary: TestSummary         # 测试汇总
    test_suites: List[TestSuite] # 测试套件
    coverage: CoverageReport     # 覆盖率报告
```

### 4.2 测试汇总

```python
class TestSummary:
    total: int           # 总测试数
    passed: int          # 通过数
    failed: int          # 失败数
    skipped: int         # 跳过数
    error: int           # 错误数
    pass_rate: float     # 通过率
```

### 4.3 测试套件

```python
class TestSuite:
    name: str                    # 套件名称
    type: str                    # 类型 (unit/integration)
    file_path: str               # 文件路径
    test_cases: List[TestCase]   # 测试用例
    duration_ms: int             # 执行时长
    status: str                  # 状态
```

### 4.4 测试用例

```python
class TestCase:
    name: str            # 用例名称
    status: str          # passed/failed/skipped/error
    duration_ms: int     # 执行时长
    error_message: str   # 错误信息
    stack_trace: str     # 堆栈信息
    assertions: int      # 断言数
```

## 5. 测试执行

### 5.1 执行流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  准备环境    │───▶│  运行测试    │───▶│  收集结果    │
└──────────────┘    └──────────────┘    └──────────────┘
                          │
                    ┌─────┴─────┐
                    │           │
               ┌────▼────┐ ┌────▼────┐
               │单元测试 │ │集成测试 │
               └────┬────┘ └────┬────┘
                    │           │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │ 覆盖率    │
                    │ 收集      │
                    └───────────┘
```

### 5.2 执行 API

```http
POST /api/v1/tests/run
Content-Type: application/json

{
  "test_generation_id": "testgen_456",
  "test_types": ["unit", "integration"],
  "parallel": true,
  "timeout": 300
}
```

### 5.3 获取执行状态

```http
GET /api/v1/tests/runs/{run_id}/status
```

响应：
```json
{
  "run_id": "run_789",
  "status": "running",
  "progress": {
    "total": 20,
    "completed": 15,
    "percentage": 75
  },
  "current_test": "test_export_large_dataset",
  "elapsed_ms": 45000
}
```

## 6. 覆盖率分析

### 6.1 覆盖率类型

| 类型 | 说明 |
|------|------|
| **Line** | 代码行覆盖率 |
| **Branch** | 分支覆盖率 |
| **Function** | 函数覆盖率 |
| **Statement** | 语句覆盖率 |

### 6.2 覆盖率报告

```python
class CoverageReport:
    total_lines: int           # 总行数
    covered_lines: int         # 覆盖行数
    line_coverage: float       # 行覆盖率
    total_branches: int        # 总分支数
    covered_branches: int      # 覆盖分支数
    branch_coverage: float     # 分支覆盖率
    total_functions: int       # 总函数数
    covered_functions: int     # 覆盖函数数
    function_coverage: float   # 函数覆盖率
    uncovered_lines: List[int] # 未覆盖行
    file_coverage: List[FileCoverage]  # 文件覆盖详情
```

### 6.3 覆盖率示例

```json
{
  "coverage": {
    "line_coverage": 85.5,
    "branch_coverage": 78.2,
    "function_coverage": 92.0,
    "file_coverage": [
      {
        "file": "src/services/export_service.py",
        "line_coverage": 88.0,
        "uncovered_lines": [45, 67, 89],
        "branch_coverage": 75.0
      }
    ]
  }
}
```

## 7. 测试报告

### 7.1 报告格式

```json
{
  "test_report": {
    "run_id": "run_789",
    "timestamp": "2024-01-15T12:30:00Z",
    "duration_ms": 65000,
    "summary": {
      "total": 25,
      "passed": 23,
      "failed": 1,
      "skipped": 1,
      "pass_rate": 0.92
    },
    "test_suites": [
      {
        "name": "单元测试",
        "type": "unit",
        "total": 20,
        "passed": 19,
        "failed": 0,
        "skipped": 1
      },
      {
        "name": "集成测试",
        "type": "integration",
        "total": 5,
        "passed": 4,
        "failed": 1,
        "skipped": 0
      }
    ],
    "failures": [
      {
        "test_name": "test_export_timeout",
        "suite": "integration",
        "error": "TimeoutError: Export took longer than 30s",
        "stack_trace": "...",
        "analysis": "大数据量导出超时，建议增加超时时间或分批处理",
        "suggestion": "修改超时配置或优化导出逻辑"
      }
    ],
    "coverage": {
      "line_coverage": 85.5,
      "branch_coverage": 78.2
    },
    "quality_gates": {
      "min_coverage_met": true,
      "no_critical_failures": true,
      "performance_acceptable": false
    },
    "recommendation": {
      "status": "needs_review",
      "message": "1个集成测试失败，需要检查超时配置",
      "next_action": "修复超时问题后重新运行测试"
    }
  }
}
```

### 7.2 报告 API

```http
GET /api/v1/tests/runs/{run_id}/report
```

### 7.3 下载报告

```http
GET /api/v1/tests/runs/{run_id}/report/download?format=html
```

## 8. 失败分析

### 8.1 失败分类

| 类别 | 说明 | 处理建议 |
|------|------|----------|
| **断言失败** | 预期与实际不符 | 检查代码逻辑 |
| **异常错误** | 未预期的异常 | 增加异常处理 |
| **超时** | 执行超时 | 优化性能 |
| **环境问题** | 依赖或配置问题 | 检查环境 |

### 8.2 智能分析

```python
async def analyze_failure(test_case: TestCase) -> FailureAnalysis:
    """分析测试失败原因"""
    
    # 1. 解析错误信息
    error_type = classify_error(test_case.error_message)
    
    # 2. 分析堆栈信息
    root_cause = analyze_stack_trace(test_case.stack_trace)
    
    # 3. 生成修复建议
    suggestion = await generate_fix_suggestion(
        error_type, 
        root_cause,
        test_case
    )
    
    return FailureAnalysis(
        error_type=error_type,
        root_cause=root_cause,
        suggestion=suggestion
    )
```

### 8.3 分析示例

```json
{
  "failure_analysis": {
    "test_name": "test_export_timeout",
    "error_type": "timeout",
    "root_cause": "大数据量导出时间超过配置的超时限制",
    "affected_code": "src/services/export_service.py:45",
    "suggestion": {
      "short_term": "增加超时配置到 60 秒",
      "long_term": "实现分批导出和流式处理"
    },
    "related_issues": ["issue_123", "issue_456"]
  }
}
```

## 9. CI/CD 集成

### 9.1 GitHub Actions 集成

```yaml
# .github/workflows/test.yml
name: Run Tests

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest tests/ \
            --junitxml=test-results.xml \
            --cov=src \
            --cov-report=xml
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml
```

### 9.2 Webhook 通知

```http
POST /api/v1/tests/webhook/github
Content-Type: application/json

{
  "action": "completed",
  "workflow_run": {
    "conclusion": "success",
    "head_sha": "abc123"
  }
}
```

### 9.3 状态回写

```python
async def update_pr_status(test_run: TestRun):
    """更新 PR 状态"""
    status = "success" if test_run.summary.pass_rate >= 1.0 else "failure"
    
    await github_api.create_status(
        sha=test_run.commit_sha,
        state=status,
        context="OpsPilot Tests",
        description=f"Tests: {test_run.summary.passed}/{test_run.summary.total} passed",
        target_url=f"{BASE_URL}/tests/runs/{test_run.id}"
    )
```

## 10. 质量门禁

### 10.1 门禁配置

```yaml
quality_gates:
  coverage:
    line: 80        # 最低行覆盖率
    branch: 70      # 最低分支覆盖率
  
  failures:
    unit: 0         # 单元测试不允许失败
    integration: 0  # 集成测试不允许失败
  
  performance:
    max_duration: 300  # 最大执行时间(秒)
```

### 10.2 门禁检查

```python
def check_quality_gates(test_run: TestRun, gates: QualityGates) -> GateResult:
    results = []
    
    # 覆盖率检查
    if test_run.coverage.line_coverage < gates.coverage.line:
        results.append(GateFailure(
            gate="line_coverage",
            expected=gates.coverage.line,
            actual=test_run.coverage.line_coverage
        ))
    
    # 失败数检查
    if test_run.summary.failed > gates.failures.unit:
        results.append(GateFailure(
            gate="unit_failures",
            expected=gates.failures.unit,
            actual=test_run.summary.failed
        ))
    
    return GateResult(
        passed=len(results) == 0,
        failures=results
    )
```

## 11. 最佳实践

### 11.1 测试编写

1. **测试独立性**：每个测试独立运行
2. **快速执行**：单个测试不超过 1 秒
3. **清晰命名**：测试名称说明测试目的
4. **充分断言**：验证所有预期结果

### 11.2 覆盖率目标

| 项目类型 | 行覆盖率 | 分支覆盖率 |
|----------|----------|------------|
| 核心模块 | >90% | >80% |
| 一般模块 | >80% | >70% |
| 工具模块 | >70% | >60% |

### 11.3 失败处理

1. **及时修复**：失败测试优先处理
2. **分析原因**：找到根本原因
3. **防止回归**：添加回归测试

## 12. 常见问题

### Q1: 测试执行很慢怎么办？

1. 启用并行执行
2. 优化测试数据准备
3. 使用 mock 替代真实服务

### Q2: 如何处理不稳定测试？

1. 分析不稳定原因
2. 添加重试机制
3. 隔离不稳定测试

### Q3: 覆盖率不够怎么办？

1. 分析未覆盖代码
2. 补充边界测试
3. 关注核心逻辑覆盖

---

*文档版本: 1.0*
*所属模块: M9 - 测试用例生成与执行*
