"""Bug 修复 Agent 服务

基于 DeerFlow 2.0 架构的 Bug 修复智能体，负责：
- 分析 Bug 问题
- 定位根因
- 生成修复方案
- 评估影响范围
"""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...models.requirement import Requirement, RequirementType
from ...models.solution import (
    BugFixSolution,
    SolutionType,
    SolutionStatus,
    ImpactAnalysis,
    ImpactLevel,
)
from ...models.knowledge import KnowledgeSearchResult


class BugFixAgentService:
    """Bug 修复 Agent 服务

    负责分析 Bug，定位根因，生成修复方案。
    当前为规则引擎实现，后续可接入 LLM 进行智能分析。
    """

    AGENT_NAME = "BugFixAgent"

    ERROR_PATTERNS = {
        "null_pointer": [
            r"null\s*pointer", r"NoneType", r"undefined", r"null\s*reference",
            r"空指针", r"为空", r"is None", r"is null"
        ],
        "memory_leak": [
            r"memory\s*leak", r"out\s*of\s*memory", r"OOM", r"内存泄漏",
            r"内存溢出", r"heap\s*overflow"
        ],
        "timeout": [
            r"timeout", r"超时", r"timed?\s*out", r"响应超时", r"连接超时"
        ],
        "connection_error": [
            r"connection\s*(refused|reset|failed)", r"连接失败", r"连接拒绝",
            r"network\s*error", r"socket\s*error", r"网络错误"
        ],
        "permission_denied": [
            r"permission\s*denied", r"access\s*denied", r"权限不足",
            r"unauthorized", r"forbidden", r"403"
        ],
        "resource_not_found": [
            r"not\s*found", r"404", r"找不到", r"不存在", r"missing"
        ],
        "data_inconsistency": [
            r"inconsisten", r"数据不一致", r"数据异常", r"脏数据", r"corrupt"
        ],
        "deadlock": [
            r"deadlock", r"死锁", r"lock\s*timeout", r"锁超时"
        ],
        "performance": [
            r"slow", r"慢", r"性能", r"performance", r"latency", r"延迟高"
        ],
    }

    ROOT_CAUSE_TEMPLATES = {
        "null_pointer": "空指针/空值引用问题，可能由于未进行空值检查或数据初始化不完整导致",
        "memory_leak": "内存泄漏问题，可能由于资源未正确释放、循环引用或大对象未及时回收导致",
        "timeout": "超时问题，可能由于网络延迟、服务响应慢、资源竞争或配置不当导致",
        "connection_error": "连接错误，可能由于网络配置问题、服务不可用、连接池耗尽或防火墙限制导致",
        "permission_denied": "权限问题，可能由于用户权限不足、Token 过期或访问控制配置错误导致",
        "resource_not_found": "资源未找到，可能由于资源已被删除、路径错误或 ID 不存在导致",
        "data_inconsistency": "数据一致性问题，可能由于并发写入、事务处理不当或数据同步失败导致",
        "deadlock": "死锁问题，可能由于锁顺序不一致、长事务或资源竞争导致",
        "performance": "性能问题，可能由于 SQL 查询未优化、缺少索引、N+1 查询或资源不足导致",
    }

    FIX_TEMPLATES = {
        "null_pointer": [
            "添加空值检查，在使用变量前进行非空验证",
            "使用 Optional 类型或默认值处理可能为空的场景",
            "检查数据初始化逻辑，确保对象正确创建",
            "添加必要的参数验证",
        ],
        "memory_leak": [
            "检查资源释放逻辑，确保所有资源在使用后正确关闭",
            "使用 with 语句或 try-finally 确保资源释放",
            "检查循环引用，必要时使用弱引用",
            "优化大对象处理，考虑分批处理或流式处理",
        ],
        "timeout": [
            "检查并优化超时配置",
            "添加重试机制和熔断保护",
            "优化慢查询和服务响应",
            "考虑异步处理长耗时操作",
        ],
        "connection_error": [
            "检查网络配置和防火墙规则",
            "增加连接池配置，处理连接复用",
            "添加服务健康检查和故障转移机制",
            "优化连接超时和重试策略",
        ],
        "permission_denied": [
            "检查用户权限配置",
            "验证 Token 有效性和刷新机制",
            "审查访问控制策略",
            "添加适当的权限验证逻辑",
        ],
        "resource_not_found": [
            "添加资源存在性检查",
            "完善错误处理和用户提示",
            "检查资源路径和 ID 的正确性",
            "添加资源缓存失效处理",
        ],
        "data_inconsistency": [
            "使用数据库事务保证一致性",
            "添加分布式锁处理并发场景",
            "实现数据校验和修复机制",
            "优化数据同步策略",
        ],
        "deadlock": [
            "统一锁获取顺序",
            "减少锁持有时间",
            "使用乐观锁替代悲观锁",
            "添加死锁检测和自动恢复",
        ],
        "performance": [
            "优化数据库查询，添加必要索引",
            "使用缓存减少重复计算",
            "实现分页和限流",
            "考虑异步处理和批量操作",
        ],
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for error_type, patterns in self.ERROR_PATTERNS.items():
            self._compiled_patterns[error_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def analyze_bug(self, requirement: Requirement) -> Dict[str, Any]:
        """分析 Bug，定位问题类型

        Args:
            requirement: 需求工单

        Returns:
            Dict: 分析结果，包含问题类型、严重程度、关键信息
        """
        text = f"{requirement.title} {requirement.description}"
        text_lower = text.lower()

        detected_types = []
        for error_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    detected_types.append(error_type)
                    break

        if not detected_types:
            detected_types = ["unknown"]

        severity = self._assess_severity(requirement)
        key_info = self._extract_key_info(text)

        return {
            "error_types": detected_types,
            "severity": severity,
            "key_info": key_info,
            "confidence": self._calculate_confidence(detected_types, text),
        }

    def _assess_severity(self, requirement: Requirement) -> str:
        """评估问题严重程度"""
        text = f"{requirement.title} {requirement.description}".lower()

        critical_indicators = ["生产", "production", "线上", "全站", "数据丢失", "宕机"]
        high_indicators = ["多用户", "频繁", "影响大", "阻塞"]

        for indicator in critical_indicators:
            if indicator in text:
                return "critical"

        for indicator in high_indicators:
            if indicator in text:
                return "high"

        return requirement.priority.value if requirement.priority else "medium"

    def _extract_key_info(self, text: str) -> Dict[str, List[str]]:
        """提取关键信息"""
        error_codes = re.findall(r'\b\d{3}\b', text)
        stack_traces = re.findall(r'at\s+[\w.]+\([\w.]+:\d+\)', text)
        file_paths = re.findall(r'[\w/]+\.(?:py|java|ts|js|go)', text)
        ip_addresses = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text)

        return {
            "error_codes": error_codes,
            "stack_traces": stack_traces,
            "file_paths": file_paths,
            "ip_addresses": ip_addresses,
        }

    def _calculate_confidence(self, detected_types: List[str], text: str) -> float:
        """计算分析置信度"""
        if "unknown" in detected_types:
            return 0.3

        match_count = sum(
            len(self._compiled_patterns.get(t, []))
            for t in detected_types
        )

        base_confidence = min(0.5 + len(detected_types) * 0.1, 0.8)
        detail_bonus = 0.1 if len(text) > 200 else 0

        return min(base_confidence + detail_bonus, 0.95)

    def find_root_cause(
        self,
        requirement: Requirement,
        knowledge_results: Optional[List[KnowledgeSearchResult]] = None
    ) -> str:
        """查找根因

        Args:
            requirement: 需求工单
            knowledge_results: 知识库检索结果

        Returns:
            str: 根因分析结果
        """
        analysis = self.analyze_bug(requirement)
        error_types = analysis["error_types"]

        root_causes = []
        for error_type in error_types:
            if error_type in self.ROOT_CAUSE_TEMPLATES:
                root_causes.append(self.ROOT_CAUSE_TEMPLATES[error_type])

        if knowledge_results:
            relevant_knowledge = self._extract_relevant_knowledge(knowledge_results)
            if relevant_knowledge:
                root_causes.append(f"\n根据知识库分析:\n{relevant_knowledge}")

        if not root_causes:
            root_causes.append(
                "根因需要进一步调查，建议检查日志、监控数据和代码变更记录"
            )

        return "\n\n".join(root_causes)

    def _extract_relevant_knowledge(
        self, knowledge_results: List[KnowledgeSearchResult]
    ) -> str:
        """从知识库结果中提取相关信息"""
        if not knowledge_results:
            return ""

        relevant = []
        for result in knowledge_results[:3]:
            if result.score > 0.5:
                relevant.append(f"- {result.title}: {result.content_snippet[:100]}...")

        return "\n".join(relevant)

    def generate_fix_solution(self, requirement: Requirement) -> BugFixSolution:
        """生成修复方案

        Args:
            requirement: 需求工单

        Returns:
            BugFixSolution: Bug 修复方案
        """
        analysis = self.analyze_bug(requirement)
        error_types = analysis["error_types"]
        root_cause = self.find_root_cause(requirement)

        fix_steps = []
        for error_type in error_types:
            if error_type in self.FIX_TEMPLATES:
                fix_steps.extend(self.FIX_TEMPLATES[error_type])

        if not fix_steps:
            fix_steps = [
                "1. 收集完整的错误日志和上下文信息",
                "2. 分析错误发生的条件和频率",
                "3. 定位问题代码位置",
                "4. 制定修复方案并评审",
                "5. 实施修复并进行充分测试",
            ]

        fix_steps = list(dict.fromkeys(fix_steps))

        impact = self.estimate_impact(requirement, analysis)
        affected_files = analysis["key_info"].get("file_paths", [])
        regression_risk = self._assess_regression_risk(error_types)
        test_cases = self._generate_test_cases(error_types)
        rollback_plan = self._generate_rollback_plan(analysis)

        solution = BugFixSolution(
            requirement_id=requirement.id,
            type=SolutionType.BUGFIX,
            title=f"[Bug修复] {requirement.title}",
            content=self._format_solution_content(
                requirement, analysis, root_cause, fix_steps
            ),
            root_cause=root_cause,
            fix_steps=fix_steps,
            regression_risk=regression_risk,
            test_cases=test_cases,
            rollback_plan=rollback_plan,
            impact_analysis=impact,
            affected_files=affected_files,
            status=SolutionStatus.DRAFT,
            created_by_agent=self.AGENT_NAME,
        )

        return solution

    def _format_solution_content(
        self,
        requirement: Requirement,
        analysis: Dict[str, Any],
        root_cause: str,
        fix_steps: List[str]
    ) -> str:
        """格式化方案内容"""
        content = f"""## Bug 修复方案

### 问题概述
{requirement.description}

### 问题分析
- **问题类型**: {', '.join(analysis['error_types'])}
- **严重程度**: {analysis['severity']}
- **分析置信度**: {analysis['confidence']:.0%}

### 根因分析
{root_cause}

### 修复步骤
"""
        for i, step in enumerate(fix_steps, 1):
            content += f"{i}. {step}\n"

        return content

    def estimate_impact(
        self,
        requirement: Requirement,
        analysis: Optional[Dict[str, Any]] = None
    ) -> ImpactAnalysis:
        """评估影响范围

        Args:
            requirement: 需求工单
            analysis: Bug 分析结果

        Returns:
            ImpactAnalysis: 影响分析结果
        """
        if analysis is None:
            analysis = self.analyze_bug(requirement)

        severity = analysis["severity"]
        level_map = {
            "critical": ImpactLevel.CRITICAL,
            "high": ImpactLevel.HIGH,
            "medium": ImpactLevel.MEDIUM,
            "low": ImpactLevel.LOW,
        }
        impact_level = level_map.get(severity, ImpactLevel.MEDIUM)

        text = f"{requirement.title} {requirement.description}".lower()
        affected_modules = []
        affected_services = []

        module_patterns = {
            "用户": "用户模块",
            "认证": "认证模块",
            "支付": "支付模块",
            "订单": "订单模块",
            "数据库": "数据库模块",
            "缓存": "缓存模块",
            "日志": "日志模块",
            "监控": "监控模块",
        }

        for keyword, module in module_patterns.items():
            if keyword in text:
                affected_modules.append(module)

        service_patterns = {
            "api": "API 服务",
            "web": "Web 服务",
            "后台": "后台服务",
            "定时": "定时任务",
            "消息": "消息队列",
            "redis": "Redis 服务",
            "mysql": "MySQL 服务",
            "nginx": "Nginx 服务",
        }

        for keyword, service in service_patterns.items():
            if keyword in text:
                affected_services.append(service)

        risk_points = []
        mitigation_strategies = []

        for error_type in analysis.get("error_types", []):
            if error_type == "data_inconsistency":
                risk_points.append("数据一致性可能受影响")
                mitigation_strategies.append("修复前备份相关数据")
            elif error_type == "performance":
                risk_points.append("性能修复可能影响其他功能")
                mitigation_strategies.append("分步发布，监控性能指标")
            elif error_type == "deadlock":
                risk_points.append("锁相关修改需要充分测试")
                mitigation_strategies.append("在测试环境进行并发压测")

        return ImpactAnalysis(
            level=impact_level,
            scope=f"影响 {len(affected_modules)} 个模块，{len(affected_services)} 个服务",
            affected_modules=affected_modules,
            affected_services=affected_services,
            risk_points=risk_points,
            mitigation_strategies=mitigation_strategies,
        )

    def _assess_regression_risk(self, error_types: List[str]) -> str:
        """评估回归风险"""
        high_risk_types = ["data_inconsistency", "deadlock", "memory_leak"]

        if any(t in high_risk_types for t in error_types):
            return "高风险: 修改涉及核心逻辑，建议进行完整回归测试，包括压力测试和边界条件测试"

        medium_risk_types = ["connection_error", "timeout", "performance"]
        if any(t in medium_risk_types for t in error_types):
            return "中风险: 修改可能影响系统稳定性，建议进行针对性回归测试"

        return "低风险: 修改范围有限，建议进行基本功能验证"

    def _generate_test_cases(self, error_types: List[str]) -> List[str]:
        """生成测试用例建议"""
        test_cases = ["验证修复后问题不再复现"]

        test_case_templates = {
            "null_pointer": "测试空值输入场景",
            "memory_leak": "进行内存泄漏检测测试",
            "timeout": "测试超时边界条件",
            "connection_error": "测试网络异常恢复",
            "permission_denied": "测试权限边界场景",
            "resource_not_found": "测试资源不存在处理",
            "data_inconsistency": "测试并发数据操作",
            "deadlock": "测试并发锁竞争场景",
            "performance": "进行性能基准测试",
        }

        for error_type in error_types:
            if error_type in test_case_templates:
                test_cases.append(test_case_templates[error_type])

        test_cases.append("执行相关模块的自动化测试用例")

        return test_cases

    def _generate_rollback_plan(self, analysis: Dict[str, Any]) -> str:
        """生成回滚方案"""
        severity = analysis.get("severity", "medium")

        if severity == "critical":
            return """紧急回滚方案:
1. 立即回退代码到上一稳定版本
2. 回滚数据库变更（如有）
3. 清理可能产生的脏数据
4. 通知相关团队和用户
5. 分析回滚原因，制定改进措施"""

        return """标准回滚方案:
1. 通过发布系统回退到上一版本
2. 验证服务恢复正常
3. 记录回滚原因和后续处理计划"""


bugfix_agent_service = BugFixAgentService()
