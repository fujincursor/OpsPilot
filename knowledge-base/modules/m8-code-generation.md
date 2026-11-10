# M8: 代码生成与校验模块

## 1. 模块概述

代码生成与校验模块负责根据审核通过的方案自动生成代码，并进行质量校验。

### 1.1 核心功能

- 代码自动生成
- Sandbox 安全执行
- 代码质量检查
- Diff 预览展示
- 代码提交准备

### 1.2 模块定位

```
审核通过的方案 → 代码生成与校验 → 可提交的代码
                       │
                       ├─ 代码生成 → 基于方案生成代码
                       │
                       ├─ Sandbox 执行 → 安全环境验证
                       │
                       ├─ 质量检查 → Lint/类型检查
                       │
                       └─ Diff 预览 → 变更确认
```

## 2. 代码生成 Agent

### 2.1 Agent 配置

```yaml
name: codegen_agent
display_name: 代码生成 Agent
description: 根据设计方案生成代码
skills:
  - code-generation
  - test-execution
settings:
  model: gpt-4o
  temperature: 0.2  # 低温度，保证代码稳定性
  max_iterations: 10
```

### 2.2 code-generation Skill

Skill 核心内容：

```markdown
# code-generation Skill

## 生成流程

### 第一阶段：准备工作
1. 读取设计方案
2. 分析现有代码结构
3. 理解项目编码规范

### 第二阶段：代码实现
1. 代码结构规划
2. 编写业务代码
3. 编写测试代码

### 第三阶段：质量检查
1. 静态代码分析
2. 类型检查
3. 安全扫描
```

## 3. 代码生成流程

### 3.1 生成流程图

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  读取方案    │───▶│  分析上下文  │───▶│  生成代码    │
└──────────────┘    └──────────────┘    └──────────────┘
                                              │
┌──────────────┐    ┌──────────────┐          │
│  完成        │◀───│  质量检查    │◀─────────┘
└──────────────┘    └──────────────┘
```

### 3.2 生成请求

```http
POST /api/v1/codegen/generate
Content-Type: application/json

{
  "solution_id": "sol_123",
  "options": {
    "generate_tests": true,
    "generate_docs": true,
    "target_language": "python",
    "style_guide": "pep8"
  }
}
```

### 3.3 生成结果

```python
class CodeGenerationResult:
    id: str                        # 生成 ID
    solution_id: str               # 方案 ID
    status: str                    # 状态
    files: List[GeneratedFile]     # 生成的文件
    tests: List[GeneratedTest]     # 生成的测试
    docs: GeneratedDocs            # 生成的文档
    quality_report: QualityReport  # 质量报告
    created_at: datetime           # 创建时间
```

## 4. 生成的代码结构

### 4.1 文件模型

```python
class GeneratedFile:
    path: str                # 文件路径
    content: str             # 文件内容
    action: str              # create/modify/delete
    language: str            # 编程语言
    original_content: str    # 原始内容（修改时）
    diff: str                # 差异对比
    line_count: int          # 代码行数
```

### 4.2 示例输出

```json
{
  "files": [
    {
      "path": "src/services/export_service.py",
      "action": "create",
      "language": "python",
      "content": "from typing import List, Optional\nimport csv\n\nclass ExportService:\n    \"\"\"数据导出服务\"\"\"\n    \n    async def export_users(\n        self,\n        fields: List[str],\n        format: str = 'csv'\n    ) -> str:\n        \"\"\"导出用户数据\"\"\"\n        # 实现代码...",
      "line_count": 85
    },
    {
      "path": "src/api/routes/export.py",
      "action": "create",
      "language": "python",
      "content": "from fastapi import APIRouter\n\nrouter = APIRouter(prefix='/exports')\n\n@router.post('')\nasync def create_export():\n    ...",
      "line_count": 45
    }
  ]
}
```

## 5. Sandbox 安全执行

### 5.1 Sandbox 架构

```
┌─────────────────────────────────────────────────────┐
│                    Host System                       │
│  ┌───────────────────────────────────────────────┐  │
│  │              Docker Container                  │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │            Sandbox Environment           │  │  │
│  │  │  • 无特权模式                           │  │  │
│  │  │  • 禁用所有 capabilities                │  │  │
│  │  │  • 只读文件系统（除工作目录）           │  │  │
│  │  │  • 内存限制：512MB                      │  │  │
│  │  │  • CPU 限制：1 core                     │  │  │
│  │  │  • 网络隔离                             │  │  │
│  │  │  • 执行超时：300s                       │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 5.2 Sandbox 配置

```yaml
sandbox:
  mode: docker
  config:
    image: python:3.11-slim
    timeout: 300
    memory_limit: 512m
    cpu_limit: 1
    network_mode: none
    read_only: true
    working_dir: /workspace
    volumes:
      - type: tmpfs
        target: /workspace
        size: 100m
```

### 5.3 执行 API

```http
POST /api/v1/codegen/sandbox/execute
Content-Type: application/json

{
  "code_generation_id": "gen_123",
  "command": "python -m pytest tests/ -v",
  "timeout": 60
}
```

响应：
```json
{
  "execution_id": "exec_456",
  "status": "completed",
  "exit_code": 0,
  "stdout": "===== test session starts =====\n...",
  "stderr": "",
  "duration_ms": 2500
}
```

### 5.4 安全限制

| 限制项 | 值 | 说明 |
|--------|-----|------|
| 执行超时 | 300s | 单次执行最大时间 |
| 内存限制 | 512MB | 容器内存上限 |
| CPU 限制 | 1 core | CPU 使用限制 |
| 磁盘空间 | 100MB | 工作目录大小 |
| 网络 | 禁用 | 隔离网络访问 |

## 6. 代码质量检查

### 6.1 检查项目

| 检查类型 | 工具 | 说明 |
|----------|------|------|
| **Lint** | Ruff/ESLint | 代码风格检查 |
| **类型检查** | MyPy/TypeScript | 类型正确性 |
| **安全扫描** | Bandit/npm audit | 安全漏洞检测 |
| **复杂度** | Radon/Complexity | 代码复杂度 |
| **覆盖率** | Coverage.py/Jest | 测试覆盖率 |

### 6.2 质量报告

```python
class QualityReport:
    lint_passed: bool              # Lint 是否通过
    lint_issues: List[LintIssue]   # Lint 问题列表
    type_check_passed: bool        # 类型检查是否通过
    type_errors: List[TypeError]   # 类型错误列表
    security_passed: bool          # 安全检查是否通过
    security_issues: List[SecurityIssue]  # 安全问题
    complexity_score: float        # 复杂度分数
    test_coverage: float           # 测试覆盖率
    overall_score: float           # 综合评分
```

### 6.3 质量报告示例

```json
{
  "quality_report": {
    "lint_passed": true,
    "lint_issues": [],
    "type_check_passed": true,
    "type_errors": [],
    "security_passed": true,
    "security_issues": [],
    "complexity_score": 8.5,
    "test_coverage": 0.85,
    "overall_score": 0.92,
    "summary": "代码质量良好，建议增加边界测试"
  }
}
```

### 6.4 质量门禁

```yaml
quality_gates:
  lint:
    max_errors: 0
    max_warnings: 10
  
  type_check:
    required: true
    strict: false
  
  security:
    max_high: 0
    max_medium: 2
  
  coverage:
    min_line: 80
    min_branch: 70
  
  complexity:
    max_cyclomatic: 10
```

## 7. Diff 预览

### 7.1 Diff 格式

```diff
--- a/src/services/export_service.py
+++ b/src/services/export_service.py
@@ -1,5 +1,25 @@
+from typing import List, Optional
+import csv
+from io import StringIO
+
+
 class ExportService:
-    pass
+    """数据导出服务"""
+    
+    async def export_users(
+        self,
+        fields: List[str],
+        format: str = 'csv'
+    ) -> str:
+        """导出用户数据
+        
+        Args:
+            fields: 要导出的字段列表
+            format: 导出格式 (csv/xlsx)
+        
+        Returns:
+            导出文件的路径
+        """
+        # 实现代码...
```

### 7.2 Diff API

```http
GET /api/v1/codegen/{generation_id}/diff
```

响应：
```json
{
  "diffs": [
    {
      "file_path": "src/services/export_service.py",
      "action": "modify",
      "additions": 45,
      "deletions": 2,
      "diff": "--- a/src/services/export_service.py\n+++ b/src/services/export_service.py\n..."
    }
  ],
  "summary": {
    "files_changed": 3,
    "insertions": 120,
    "deletions": 5
  }
}
```

### 7.3 Diff 展示组件

```tsx
// 前端 Diff 展示组件
<DiffViewer
  oldValue={originalCode}
  newValue={generatedCode}
  splitView={true}
  showDiffOnly={false}
  useDarkTheme={false}
/>
```

## 8. 代码生成 API

### 8.1 触发代码生成

```http
POST /api/v1/codegen/generate
Content-Type: application/json

{
  "solution_id": "sol_123",
  "options": {
    "generate_tests": true,
    "generate_docs": true
  }
}
```

### 8.2 获取生成状态

```http
GET /api/v1/codegen/{generation_id}/status
```

### 8.3 获取生成结果

```http
GET /api/v1/codegen/{generation_id}
```

### 8.4 执行质量检查

```http
POST /api/v1/codegen/{generation_id}/check
```

### 8.5 应用代码变更

```http
POST /api/v1/codegen/{generation_id}/apply
Content-Type: application/json

{
  "files": ["src/services/export_service.py"],
  "create_branch": true,
  "branch_name": "feature/export-users"
}
```

## 9. 测试代码生成

### 9.1 测试生成策略

```python
def generate_tests(code: str, config: TestConfig) -> List[TestCase]:
    tests = []
    
    # 1. 分析代码结构
    functions = parse_functions(code)
    
    # 2. 为每个函数生成测试
    for func in functions:
        # 正常流程测试
        tests.append(generate_happy_path_test(func))
        
        # 边界条件测试
        tests.extend(generate_boundary_tests(func))
        
        # 异常情况测试
        tests.extend(generate_error_tests(func))
    
    return tests
```

### 9.2 生成的测试示例

```python
# tests/test_export_service.py

import pytest
from src.services.export_service import ExportService

class TestExportService:
    @pytest.fixture
    def service(self):
        return ExportService()
    
    async def test_export_users_csv_success(self, service):
        """测试 CSV 导出成功"""
        result = await service.export_users(
            fields=['id', 'name', 'email'],
            format='csv'
        )
        assert result is not None
        assert result.endswith('.csv')
    
    async def test_export_users_empty_fields(self, service):
        """测试空字段列表"""
        with pytest.raises(ValueError):
            await service.export_users(fields=[], format='csv')
    
    async def test_export_users_invalid_format(self, service):
        """测试无效格式"""
        with pytest.raises(ValueError):
            await service.export_users(
                fields=['id'],
                format='invalid'
            )
```

## 10. 最佳实践

### 10.1 代码生成建议

1. **方案要详细**
   - 详细的设计方案生成更好的代码
   - 包含示例有助于理解意图

2. **审查生成的代码**
   - AI 生成的代码需要人工审查
   - 关注边界情况和异常处理

3. **迭代优化**
   - 可以多次生成并选择最佳结果
   - 反馈帮助改进

### 10.2 Sandbox 使用建议

1. **不要禁用安全限制**
2. **监控资源使用**
3. **定期清理临时文件**

## 11. 常见问题

### Q1: 代码生成需要多长时间？

通常 10-60 秒，取决于代码量和复杂度。

### Q2: 生成的代码质量如何？

- 基础框架质量较好
- 复杂业务逻辑需要人工优化
- 始终需要人工审查

### Q3: 支持哪些编程语言？

目前主要支持：
- Python
- TypeScript/JavaScript
- Java
- Go

---

*文档版本: 1.0*
*所属模块: M8 - 代码生成与校验*
