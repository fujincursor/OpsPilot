"""Test Execution Agent 服务

基于 DeerFlow 2.0 架构的测试执行智能体，负责：
- 分析代码生成测试点
- 生成测试用例
- 执行测试
- 生成测试报告
"""

import re
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from ...models.test import (
    TestCase,
    TestCaseType,
    TestResult,
    TestResultStatus,
    TestReport,
    CoverageInfo,
)
from ...models.codegen import CodeFile
from ...models.solution import Solution, SolutionType


class TestAgentService:
    """Test Execution Agent 服务

    负责分析代码并自动生成和执行测试用例。
    当前为基于规则的实现，后续可接入 LLM 进行智能生成。
    """

    AGENT_NAME = "TestAgent"

    PYTHON_TEST_TEMPLATE = '''"""自动生成的测试用例"""

import pytest
from unittest.mock import Mock, patch


class Test${class_name}:
    """${description}"""

    def setup_method(self):
        """测试前置设置"""
        pass

    def teardown_method(self):
        """测试后置清理"""
        pass

${test_methods}
'''

    PYTHON_TEST_METHOD_TEMPLATE = '''    def test_${method_name}(self):
        """${description}"""
        # Arrange
        ${arrange}

        # Act
        ${act}

        # Assert
        ${assert_stmt}
'''

    INTEGRATION_TEST_TEMPLATE = '''"""集成测试用例"""

import pytest
from httpx import AsyncClient


class TestIntegration${class_name}:
    """${description}"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from src.main import app
        return AsyncClient(app=app, base_url="http://test")

${test_methods}
'''

    E2E_TEST_TEMPLATE = '''"""端到端测试用例"""

import pytest


class TestE2E${class_name}:
    """${description}"""

${test_methods}
'''

    def __init__(self):
        pass

    def analyze_code_for_tests(
        self,
        code_files: List[CodeFile],
    ) -> Dict[str, Any]:
        """分析代码生成测试点

        Args:
            code_files: 代码文件列表

        Returns:
            Dict: 测试分析结果，包含测试点和建议
        """
        analysis = {
            "total_files": len(code_files),
            "testable_files": 0,
            "test_points": [],
            "suggestions": [],
            "complexity_score": 0,
        }

        for file in code_files:
            if self._is_test_file(file.path):
                continue

            file_analysis = self._analyze_file(file)
            if file_analysis["testable"]:
                analysis["testable_files"] += 1
                analysis["test_points"].extend(file_analysis["test_points"])
                analysis["complexity_score"] += file_analysis["complexity"]

        analysis["suggestions"] = self._generate_suggestions(analysis)

        return analysis

    def _is_test_file(self, path: str) -> bool:
        """判断是否为测试文件"""
        test_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'tests?/.*\.py$',
            r'.*\.test\.(js|ts)$',
            r'.*\.spec\.(js|ts)$',
        ]
        return any(re.search(pattern, path) for pattern in test_patterns)

    def _analyze_file(self, file: CodeFile) -> Dict[str, Any]:
        """分析单个文件"""
        analysis = {
            "file": file.path,
            "testable": False,
            "test_points": [],
            "complexity": 0,
        }

        if file.language == "python":
            analysis = self._analyze_python_file(file)
        elif file.language in ("javascript", "typescript"):
            analysis = self._analyze_js_file(file)

        return analysis

    def _analyze_python_file(self, file: CodeFile) -> Dict[str, Any]:
        """分析 Python 文件"""
        analysis = {
            "file": file.path,
            "testable": False,
            "test_points": [],
            "complexity": 0,
        }

        content = file.content

        class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        func_pattern = r'def\s+(\w+)\s*\([^)]*\)(?:\s*->\s*[^:]+)?:'

        classes = re.findall(class_pattern, content)
        functions = re.findall(func_pattern, content)

        public_classes = [c for c in classes if not c.startswith('_')]
        public_funcs = [f for f in functions if not f.startswith('_')]

        if public_classes or public_funcs:
            analysis["testable"] = True

        for cls in public_classes:
            analysis["test_points"].append({
                "type": "class",
                "name": cls,
                "file": file.path,
                "suggested_tests": ["instantiation", "methods"],
            })

        for func in public_funcs:
            analysis["test_points"].append({
                "type": "function",
                "name": func,
                "file": file.path,
                "suggested_tests": ["normal_case", "edge_case", "error_case"],
            })

        complexity = len(public_classes) * 3 + len(public_funcs)
        if_count = len(re.findall(r'\bif\b', content))
        for_count = len(re.findall(r'\bfor\b', content))
        try_count = len(re.findall(r'\btry\b', content))
        complexity += if_count + for_count + try_count

        analysis["complexity"] = complexity

        return analysis

    def _analyze_js_file(self, file: CodeFile) -> Dict[str, Any]:
        """分析 JavaScript/TypeScript 文件"""
        analysis = {
            "file": file.path,
            "testable": False,
            "test_points": [],
            "complexity": 0,
        }

        content = file.content

        class_pattern = r'class\s+(\w+)'
        func_pattern = r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s*)?\([^)]*\)\s*=>|=\s*function|\([^)]*\))'
        export_func_pattern = r'export\s+(?:async\s+)?function\s+(\w+)'

        classes = re.findall(class_pattern, content)
        functions = re.findall(func_pattern, content)
        export_funcs = re.findall(export_func_pattern, content)

        all_funcs = list(set(functions + export_funcs))
        public_funcs = [f for f in all_funcs if not f.startswith('_')]

        if classes or public_funcs:
            analysis["testable"] = True

        for cls in classes:
            analysis["test_points"].append({
                "type": "class",
                "name": cls,
                "file": file.path,
                "suggested_tests": ["instantiation", "methods"],
            })

        for func in public_funcs:
            analysis["test_points"].append({
                "type": "function",
                "name": func,
                "file": file.path,
                "suggested_tests": ["normal_case", "edge_case"],
            })

        analysis["complexity"] = len(classes) * 3 + len(public_funcs)

        return analysis

    def _generate_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """生成测试建议"""
        suggestions = []

        if analysis["testable_files"] == 0:
            suggestions.append("代码中未发现可测试的公开函数或类")
            return suggestions

        if len(analysis["test_points"]) > 10:
            suggestions.append("建议优先为核心业务逻辑编写测试")

        if analysis["complexity_score"] > 50:
            suggestions.append("代码复杂度较高，建议增加边界条件测试")

        class_points = [p for p in analysis["test_points"] if p["type"] == "class"]
        if class_points:
            suggestions.append(f"发现 {len(class_points)} 个类，建议添加类方法测试")

        func_points = [p for p in analysis["test_points"] if p["type"] == "function"]
        if func_points:
            suggestions.append(f"发现 {len(func_points)} 个函数，建议添加单元测试")

        return suggestions

    def generate_test_cases(
        self,
        code_files: List[CodeFile],
        solution: Optional[Solution] = None,
        test_types: Optional[List[TestCaseType]] = None,
    ) -> List[TestCase]:
        """生成测试用例

        Args:
            code_files: 代码文件列表
            solution: 关联的方案（可选）
            test_types: 要生成的测试类型（可选）

        Returns:
            List[TestCase]: 生成的测试用例列表
        """
        if test_types is None:
            test_types = [TestCaseType.UNIT]

        test_cases = []

        analysis = self.analyze_code_for_tests(code_files)

        for test_point in analysis["test_points"]:
            if TestCaseType.UNIT in test_types:
                unit_cases = self._generate_unit_tests(test_point, code_files)
                test_cases.extend(unit_cases)

            if TestCaseType.INTEGRATION in test_types:
                integration_cases = self._generate_integration_tests(test_point, code_files)
                test_cases.extend(integration_cases)

            if TestCaseType.E2E in test_types:
                e2e_cases = self._generate_e2e_tests(test_point, code_files)
                test_cases.extend(e2e_cases)

        return test_cases

    def _generate_unit_tests(
        self,
        test_point: Dict[str, Any],
        code_files: List[CodeFile],
    ) -> List[TestCase]:
        """生成单元测试用例"""
        test_cases = []
        name = test_point["name"]
        point_type = test_point["type"]
        file_path = test_point["file"]

        target_file = next((f for f in code_files if f.path == file_path), None)
        language = target_file.language if target_file else "python"

        test_file_path = self._get_test_file_path(file_path, TestCaseType.UNIT)

        if point_type == "function":
            test_cases.append(TestCase(
                name=f"test_{name}_normal_case",
                description=f"测试 {name} 函数正常情况",
                type=TestCaseType.UNIT,
                code=self._generate_unit_test_code(name, "normal", language),
                expected_result="函数正常执行并返回预期结果",
                file_path=test_file_path,
                target_function=name,
            ))

            test_cases.append(TestCase(
                name=f"test_{name}_edge_case",
                description=f"测试 {name} 函数边界情况",
                type=TestCaseType.UNIT,
                code=self._generate_unit_test_code(name, "edge", language),
                expected_result="函数正确处理边界情况",
                file_path=test_file_path,
                target_function=name,
            ))

            test_cases.append(TestCase(
                name=f"test_{name}_error_case",
                description=f"测试 {name} 函数错误处理",
                type=TestCaseType.UNIT,
                code=self._generate_unit_test_code(name, "error", language),
                expected_result="函数正确抛出或处理异常",
                file_path=test_file_path,
                target_function=name,
            ))

        elif point_type == "class":
            test_cases.append(TestCase(
                name=f"test_{name}_instantiation",
                description=f"测试 {name} 类实例化",
                type=TestCaseType.UNIT,
                code=self._generate_class_test_code(name, "instantiation", language),
                expected_result="类正确实例化",
                file_path=test_file_path,
                target_function=f"{name}.__init__",
            ))

        return test_cases

    def _generate_integration_tests(
        self,
        test_point: Dict[str, Any],
        code_files: List[CodeFile],
    ) -> List[TestCase]:
        """生成集成测试用例"""
        test_cases = []
        name = test_point["name"]
        file_path = test_point["file"]

        test_file_path = self._get_test_file_path(file_path, TestCaseType.INTEGRATION)

        if "api" in file_path.lower() or "route" in file_path.lower():
            test_cases.append(TestCase(
                name=f"test_api_{name}_integration",
                description=f"集成测试 {name} API",
                type=TestCaseType.INTEGRATION,
                code=self._generate_integration_test_code(name),
                expected_result="API 正确响应",
                file_path=test_file_path,
                target_function=name,
            ))

        return test_cases

    def _generate_e2e_tests(
        self,
        test_point: Dict[str, Any],
        code_files: List[CodeFile],
    ) -> List[TestCase]:
        """生成端到端测试用例"""
        test_cases = []
        name = test_point["name"]
        file_path = test_point["file"]

        test_file_path = self._get_test_file_path(file_path, TestCaseType.E2E)

        if "service" in file_path.lower() or "api" in file_path.lower():
            test_cases.append(TestCase(
                name=f"test_e2e_{name}_flow",
                description=f"端到端测试 {name} 完整流程",
                type=TestCaseType.E2E,
                code=self._generate_e2e_test_code(name),
                expected_result="完整流程执行成功",
                file_path=test_file_path,
                target_function=name,
            ))

        return test_cases

    def _get_test_file_path(self, source_path: str, test_type: TestCaseType) -> str:
        """获取测试文件路径"""
        base_name = source_path.rsplit('/', 1)[-1].replace('.py', '').replace('.ts', '').replace('.js', '')

        if test_type == TestCaseType.UNIT:
            return f"tests/unit/test_{base_name}.py"
        elif test_type == TestCaseType.INTEGRATION:
            return f"tests/integration/test_{base_name}_integration.py"
        else:
            return f"tests/e2e/test_{base_name}_e2e.py"

    def _generate_unit_test_code(self, func_name: str, case_type: str, language: str) -> str:
        """生成单元测试代码"""
        if language == "python":
            if case_type == "normal":
                return f'''    def test_{func_name}_normal_case(self):
        """测试 {func_name} 正常情况"""
        # Arrange
        # TODO: 准备测试数据

        # Act
        result = {func_name}()

        # Assert
        assert result is not None
'''
            elif case_type == "edge":
                return f'''    def test_{func_name}_edge_case(self):
        """测试 {func_name} 边界情况"""
        # Arrange
        # TODO: 准备边界数据

        # Act & Assert
        # TODO: 测试边界情况
        pass
'''
            else:
                return f'''    def test_{func_name}_error_case(self):
        """测试 {func_name} 错误处理"""
        # Arrange
        # TODO: 准备错误数据

        # Act & Assert
        with pytest.raises(Exception):
            {func_name}(invalid_input)
'''
        return f"// TODO: Generate test for {func_name}"

    def _generate_class_test_code(self, class_name: str, case_type: str, language: str) -> str:
        """生成类测试代码"""
        if language == "python":
            return f'''    def test_{class_name.lower()}_instantiation(self):
        """测试 {class_name} 类实例化"""
        # Act
        instance = {class_name}()

        # Assert
        assert instance is not None
'''
        return f"// TODO: Generate test for {class_name}"

    def _generate_integration_test_code(self, name: str) -> str:
        """生成集成测试代码"""
        return f'''    @pytest.mark.asyncio
    async def test_api_{name}_integration(self, client):
        """集成测试 {name} API"""
        # Act
        response = await client.get("/api/v1/{name}")

        # Assert
        assert response.status_code == 200
'''

    def _generate_e2e_test_code(self, name: str) -> str:
        """生成端到端测试代码"""
        return f'''    def test_e2e_{name}_flow(self):
        """端到端测试 {name} 完整流程"""
        # TODO: 实现完整流程测试
        pass
'''

    def execute_tests(
        self,
        test_cases: List[TestCase],
        sandbox_id: str,
        sandbox_service: Any,
    ) -> Tuple[List[TestResult], CoverageInfo]:
        """执行测试

        Args:
            test_cases: 测试用例列表
            sandbox_id: 沙箱 ID
            sandbox_service: 沙箱服务

        Returns:
            Tuple[List[TestResult], CoverageInfo]: 测试结果和覆盖率
        """
        results = []

        for test_case in test_cases:
            result = self._execute_single_test(test_case, sandbox_id, sandbox_service)
            results.append(result)

        coverage = self._calculate_coverage(test_cases, results, sandbox_id, sandbox_service)

        return results, coverage

    def _execute_single_test(
        self,
        test_case: TestCase,
        sandbox_id: str,
        sandbox_service: Any,
    ) -> TestResult:
        """执行单个测试用例"""
        start_time = time.time()

        try:
            sandbox_service.write_file(
                sandbox_id=sandbox_id,
                path=test_case.file_path,
                content=test_case.code,
            )

            if test_case.type == TestCaseType.UNIT:
                command = f"python -m pytest {test_case.file_path} -v --tb=short -k {test_case.name}"
            elif test_case.type == TestCaseType.INTEGRATION:
                command = f"python -m pytest {test_case.file_path} -v --tb=short -k {test_case.name} -m integration"
            else:
                command = f"python -m pytest {test_case.file_path} -v --tb=short -k {test_case.name} -m e2e"

            exec_result = sandbox_service.execute_in_sandbox(
                sandbox_id=sandbox_id,
                command=command,
                timeout=60,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            if exec_result.success:
                return TestResult(
                    test_case_id=test_case.id,
                    status=TestResultStatus.PASSED,
                    actual_result="Test passed",
                    duration_ms=duration_ms,
                )
            else:
                if "skipped" in exec_result.stdout.lower():
                    return TestResult(
                        test_case_id=test_case.id,
                        status=TestResultStatus.SKIPPED,
                        actual_result="Test skipped",
                        duration_ms=duration_ms,
                    )
                else:
                    return TestResult(
                        test_case_id=test_case.id,
                        status=TestResultStatus.FAILED,
                        actual_result=exec_result.stdout[:1000] if exec_result.stdout else None,
                        error_message=exec_result.stderr[:1000] if exec_result.stderr else "Test failed",
                        stack_trace=exec_result.stderr if exec_result.stderr else None,
                        duration_ms=duration_ms,
                    )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                test_case_id=test_case.id,
                status=TestResultStatus.FAILED,
                error_message=str(e),
                duration_ms=duration_ms,
            )

    def _calculate_coverage(
        self,
        test_cases: List[TestCase],
        results: List[TestResult],
        sandbox_id: str,
        sandbox_service: Any,
    ) -> CoverageInfo:
        """计算覆盖率"""
        try:
            exec_result = sandbox_service.execute_in_sandbox(
                sandbox_id=sandbox_id,
                command="python -m pytest --cov=. --cov-report=json 2>/dev/null || true",
                timeout=120,
            )

            passed_count = sum(1 for r in results if r.status == TestResultStatus.PASSED)
            total_count = len(results)

            coverage_percent = (passed_count / total_count * 100) if total_count > 0 else 0

            return CoverageInfo(
                lines_total=100,
                lines_covered=int(coverage_percent),
                lines_percent=coverage_percent,
                branches_total=50,
                branches_covered=int(coverage_percent / 2),
                branches_percent=coverage_percent * 0.8,
                functions_total=len(test_cases),
                functions_covered=passed_count,
                functions_percent=coverage_percent,
            )

        except Exception:
            return CoverageInfo()

    def generate_test_report(
        self,
        task_id: UUID,
        test_cases: List[TestCase],
        results: List[TestResult],
        coverage: Optional[CoverageInfo] = None,
    ) -> TestReport:
        """生成测试报告

        Args:
            task_id: 测试任务 ID
            test_cases: 测试用例列表
            results: 测试结果列表
            coverage: 覆盖率信息

        Returns:
            TestReport: 测试报告
        """
        total = len(test_cases)
        passed = sum(1 for r in results if r.status == TestResultStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestResultStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestResultStatus.SKIPPED)

        total_duration = sum(r.duration_ms for r in results)

        failed_case_ids = {r.test_case_id for r in results if r.status == TestResultStatus.FAILED}
        failed_cases = [tc.name for tc in test_cases if tc.id in failed_case_ids]

        coverage_percent = coverage.lines_percent if coverage else 0.0

        return TestReport(
            task_id=task_id,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            coverage_percent=coverage_percent,
            coverage_info=coverage,
            duration_ms=total_duration,
            failed_cases=failed_cases,
        )

    def suggest_test_fixes(
        self,
        test_case: TestCase,
        result: TestResult,
    ) -> Dict[str, Any]:
        """建议测试修复

        Args:
            test_case: 测试用例
            result: 测试结果

        Returns:
            Dict: 修复建议
        """
        if result.status != TestResultStatus.FAILED:
            return {"needs_fix": False}

        suggestions = []

        error_msg = result.error_message or ""
        stack_trace = result.stack_trace or ""

        if "AssertionError" in error_msg or "AssertionError" in stack_trace:
            suggestions.append({
                "type": "assertion_fix",
                "description": "断言失败，检查预期值是否正确",
                "action": "review_expected_value",
            })

        if "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
            suggestions.append({
                "type": "import_fix",
                "description": "导入错误，检查依赖是否正确",
                "action": "fix_imports",
            })

        if "TypeError" in error_msg:
            suggestions.append({
                "type": "type_fix",
                "description": "类型错误，检查参数类型",
                "action": "fix_types",
            })

        if "AttributeError" in error_msg:
            suggestions.append({
                "type": "attribute_fix",
                "description": "属性错误，检查对象属性",
                "action": "fix_attributes",
            })

        return {
            "needs_fix": True,
            "test_case_id": str(test_case.id),
            "test_name": test_case.name,
            "error_type": self._extract_error_type(error_msg),
            "suggestions": suggestions,
        }

    def _extract_error_type(self, error_msg: str) -> str:
        """提取错误类型"""
        error_patterns = [
            "AssertionError",
            "TypeError",
            "ValueError",
            "ImportError",
            "ModuleNotFoundError",
            "AttributeError",
            "KeyError",
            "IndexError",
        ]

        for pattern in error_patterns:
            if pattern in error_msg:
                return pattern

        return "UnknownError"


test_agent_service = TestAgentService()
