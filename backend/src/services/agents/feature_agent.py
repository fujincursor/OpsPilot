"""Feature 设计 Agent 服务

基于 DeerFlow 2.0 架构的功能设计智能体，负责：
- 分析功能需求
- 设计系统架构
- 设计 API 接口
- 生成设计文档
"""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...models.requirement import Requirement, RequirementType
from ...models.solution import (
    FeatureDesignSolution,
    SolutionType,
    SolutionStatus,
    ImpactAnalysis,
    ImpactLevel,
    APIEndpoint,
    DatabaseChange,
    ArchitectureComponent,
)
from ...models.knowledge import KnowledgeSearchResult


class FeatureDesignAgentService:
    """Feature 设计 Agent 服务

    负责分析需求，设计架构和 API，生成设计文档。
    当前为规则引擎实现，后续可接入 LLM 进行智能分析。
    """

    AGENT_NAME = "FeatureDesignAgent"

    FEATURE_PATTERNS = {
        "crud": [
            r"增删改查", r"CRUD", r"管理", r"列表", r"详情", r"新增", r"删除", r"修改"
        ],
        "authentication": [
            r"登录", r"认证", r"授权", r"权限", r"auth", r"login", r"token", r"JWT"
        ],
        "file_upload": [
            r"上传", r"文件", r"图片", r"附件", r"upload", r"file", r"image"
        ],
        "search": [
            r"搜索", r"检索", r"查询", r"筛选", r"search", r"query", r"filter"
        ],
        "notification": [
            r"通知", r"消息", r"告警", r"推送", r"notification", r"message", r"alert"
        ],
        "report": [
            r"报表", r"统计", r"分析", r"报告", r"report", r"statistics", r"analytics"
        ],
        "integration": [
            r"集成", r"对接", r"接入", r"同步", r"integration", r"sync"
        ],
        "workflow": [
            r"工作流", r"流程", r"审批", r"workflow", r"process", r"approval"
        ],
        "scheduling": [
            r"定时", r"调度", r"计划", r"schedule", r"cron", r"job"
        ],
        "monitoring": [
            r"监控", r"监测", r"告警", r"monitor", r"metric", r"alert"
        ],
    }

    COMPONENT_TEMPLATES = {
        "crud": [
            ArchitectureComponent(
                name="数据访问层",
                type="repository",
                description="负责数据的持久化操作",
                dependencies=["数据库"],
                interfaces=["create", "read", "update", "delete", "list"],
            ),
            ArchitectureComponent(
                name="业务逻辑层",
                type="service",
                description="实现核心业务逻辑",
                dependencies=["数据访问层"],
                interfaces=["业务方法"],
            ),
            ArchitectureComponent(
                name="API 控制层",
                type="controller",
                description="处理 HTTP 请求和响应",
                dependencies=["业务逻辑层"],
                interfaces=["REST API"],
            ),
        ],
        "authentication": [
            ArchitectureComponent(
                name="认证服务",
                type="service",
                description="处理用户认证和 Token 管理",
                dependencies=["用户存储", "Token 存储"],
                interfaces=["login", "logout", "refresh_token", "verify_token"],
            ),
            ArchitectureComponent(
                name="授权中间件",
                type="middleware",
                description="验证请求的权限",
                dependencies=["认证服务"],
                interfaces=["authenticate", "authorize"],
            ),
        ],
        "file_upload": [
            ArchitectureComponent(
                name="文件服务",
                type="service",
                description="处理文件上传、存储和访问",
                dependencies=["对象存储"],
                interfaces=["upload", "download", "delete", "get_url"],
            ),
        ],
        "notification": [
            ArchitectureComponent(
                name="通知服务",
                type="service",
                description="管理消息通知的发送和状态",
                dependencies=["消息队列", "通知渠道"],
                interfaces=["send", "broadcast", "mark_read"],
            ),
            ArchitectureComponent(
                name="通知渠道适配器",
                type="adapter",
                description="支持多种通知渠道（邮件、短信、推送）",
                dependencies=[],
                interfaces=["send_email", "send_sms", "send_push"],
            ),
        ],
    }

    API_TEMPLATES = {
        "crud": [
            APIEndpoint(
                method="GET",
                path="/{resource}",
                description="获取资源列表",
                request_body=None,
                response_body={"items": [], "total": 0, "page": 1, "page_size": 20},
            ),
            APIEndpoint(
                method="GET",
                path="/{resource}/{id}",
                description="获取单个资源详情",
                request_body=None,
                response_body={"id": "uuid", "...": "resource fields"},
            ),
            APIEndpoint(
                method="POST",
                path="/{resource}",
                description="创建资源",
                request_body={"...": "resource fields"},
                response_body={"id": "uuid", "...": "created resource"},
            ),
            APIEndpoint(
                method="PUT",
                path="/{resource}/{id}",
                description="更新资源",
                request_body={"...": "fields to update"},
                response_body={"id": "uuid", "...": "updated resource"},
            ),
            APIEndpoint(
                method="DELETE",
                path="/{resource}/{id}",
                description="删除资源",
                request_body=None,
                response_body=None,
            ),
        ],
        "authentication": [
            APIEndpoint(
                method="POST",
                path="/auth/login",
                description="用户登录",
                request_body={"username": "string", "password": "string"},
                response_body={"access_token": "string", "refresh_token": "string", "token_type": "bearer"},
            ),
            APIEndpoint(
                method="POST",
                path="/auth/logout",
                description="用户登出",
                request_body=None,
                response_body={"message": "success"},
            ),
            APIEndpoint(
                method="POST",
                path="/auth/refresh",
                description="刷新 Token",
                request_body={"refresh_token": "string"},
                response_body={"access_token": "string"},
            ),
        ],
        "file_upload": [
            APIEndpoint(
                method="POST",
                path="/files/upload",
                description="上传文件",
                request_body={"file": "binary", "category": "string"},
                response_body={"file_id": "uuid", "url": "string", "size": 0},
            ),
            APIEndpoint(
                method="GET",
                path="/files/{file_id}",
                description="获取文件信息",
                request_body=None,
                response_body={"file_id": "uuid", "filename": "string", "url": "string"},
            ),
            APIEndpoint(
                method="DELETE",
                path="/files/{file_id}",
                description="删除文件",
                request_body=None,
                response_body=None,
            ),
        ],
    }

    DB_TEMPLATES = {
        "crud": [
            DatabaseChange(
                change_type="create_table",
                table_name="{resource}",
                description="创建资源主表",
                sql_migration="""
CREATE TABLE {resource} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- 业务字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
            ),
            DatabaseChange(
                change_type="create_index",
                table_name="{resource}",
                description="创建常用索引",
                sql_migration="CREATE INDEX idx_{resource}_created_at ON {resource}(created_at);",
            ),
        ],
        "authentication": [
            DatabaseChange(
                change_type="create_table",
                table_name="user_sessions",
                description="用户会话表",
                sql_migration="""
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
""",
            ),
        ],
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for feature_type, patterns in self.FEATURE_PATTERNS.items():
            self._compiled_patterns[feature_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def analyze_requirement(self, requirement: Requirement) -> Dict[str, Any]:
        """分析需求，识别功能类型和范围

        Args:
            requirement: 需求工单

        Returns:
            Dict: 分析结果
        """
        text = f"{requirement.title} {requirement.description}"
        text_lower = text.lower()

        detected_features = []
        for feature_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    detected_features.append(feature_type)
                    break

        if not detected_features:
            detected_features = ["crud"]

        complexity = self._assess_complexity(requirement, detected_features)
        entities = self._extract_entities(text)

        return {
            "feature_types": detected_features,
            "complexity": complexity,
            "entities": entities,
            "confidence": self._calculate_confidence(detected_features, text),
        }

    def _assess_complexity(
        self, requirement: Requirement, feature_types: List[str]
    ) -> str:
        """评估功能复杂度"""
        text = f"{requirement.title} {requirement.description}".lower()

        complexity_score = len(feature_types)

        complex_indicators = ["分布式", "高并发", "大数据", "实时", "异步", "微服务"]
        for indicator in complex_indicators:
            if indicator in text:
                complexity_score += 1

        if complexity_score >= 4:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        return "low"

    def _extract_entities(self, text: str) -> List[str]:
        """提取业务实体"""
        entity_patterns = [
            r"(\w+)管理",
            r"(\w+)列表",
            r"(\w+)详情",
            r"(\w+)信息",
        ]

        entities = []
        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)

        return list(set(entities))

    def _calculate_confidence(self, feature_types: List[str], text: str) -> float:
        """计算分析置信度"""
        if not feature_types:
            return 0.3

        base_confidence = min(0.5 + len(feature_types) * 0.1, 0.8)
        detail_bonus = 0.1 if len(text) > 200 else 0

        return min(base_confidence + detail_bonus, 0.95)

    def design_architecture(
        self,
        requirement: Requirement,
        analysis: Optional[Dict[str, Any]] = None
    ) -> List[ArchitectureComponent]:
        """设计架构

        Args:
            requirement: 需求工单
            analysis: 需求分析结果

        Returns:
            List[ArchitectureComponent]: 架构组件列表
        """
        if analysis is None:
            analysis = self.analyze_requirement(requirement)

        components = []
        feature_types = analysis.get("feature_types", ["crud"])

        for feature_type in feature_types:
            if feature_type in self.COMPONENT_TEMPLATES:
                components.extend(self.COMPONENT_TEMPLATES[feature_type])

        if not components:
            components = self.COMPONENT_TEMPLATES["crud"].copy()

        seen_names = set()
        unique_components = []
        for comp in components:
            if comp.name not in seen_names:
                seen_names.add(comp.name)
                unique_components.append(comp)

        return unique_components

    def design_api(
        self,
        requirement: Requirement,
        analysis: Optional[Dict[str, Any]] = None
    ) -> List[APIEndpoint]:
        """设计 API

        Args:
            requirement: 需求工单
            analysis: 需求分析结果

        Returns:
            List[APIEndpoint]: API 端点列表
        """
        if analysis is None:
            analysis = self.analyze_requirement(requirement)

        endpoints = []
        feature_types = analysis.get("feature_types", ["crud"])
        entities = analysis.get("entities", ["resource"])

        for feature_type in feature_types:
            if feature_type in self.API_TEMPLATES:
                templates = self.API_TEMPLATES[feature_type]
                for template in templates:
                    endpoint = APIEndpoint(
                        method=template.method,
                        path=template.path,
                        description=template.description,
                        request_body=template.request_body,
                        response_body=template.response_body,
                    )
                    if entities and "{resource}" in endpoint.path:
                        resource = entities[0] if entities else "items"
                        endpoint.path = endpoint.path.replace("{resource}", resource)
                    endpoints.append(endpoint)

        if not endpoints:
            endpoints = self.API_TEMPLATES["crud"].copy()

        return endpoints

    def design_database(
        self,
        requirement: Requirement,
        analysis: Optional[Dict[str, Any]] = None
    ) -> List[DatabaseChange]:
        """设计数据库变更

        Args:
            requirement: 需求工单
            analysis: 需求分析结果

        Returns:
            List[DatabaseChange]: 数据库变更列表
        """
        if analysis is None:
            analysis = self.analyze_requirement(requirement)

        changes = []
        feature_types = analysis.get("feature_types", ["crud"])
        entities = analysis.get("entities", ["resource"])

        for feature_type in feature_types:
            if feature_type in self.DB_TEMPLATES:
                templates = self.DB_TEMPLATES[feature_type]
                for template in templates:
                    table_name = template.table_name
                    sql = template.sql_migration or ""

                    if entities and "{resource}" in table_name:
                        resource = entities[0] if entities else "items"
                        table_name = table_name.replace("{resource}", resource)
                        sql = sql.replace("{resource}", resource)

                    change = DatabaseChange(
                        change_type=template.change_type,
                        table_name=table_name,
                        description=template.description,
                        sql_migration=sql,
                    )
                    changes.append(change)

        return changes

    def generate_design_doc(self, requirement: Requirement) -> FeatureDesignSolution:
        """生成设计文档

        Args:
            requirement: 需求工单

        Returns:
            FeatureDesignSolution: 功能设计方案
        """
        analysis = self.analyze_requirement(requirement)

        architecture = self.design_architecture(requirement, analysis)
        api_design = self.design_api(requirement, analysis)
        database_changes = self.design_database(requirement, analysis)

        impact = self._estimate_impact(requirement, analysis)
        dependencies = self._identify_dependencies(analysis)
        implementation_phases = self._plan_implementation_phases(analysis)
        non_functional_requirements = self._define_nfr(analysis)

        solution = FeatureDesignSolution(
            requirement_id=requirement.id,
            type=SolutionType.FEATURE_DESIGN,
            title=f"[功能设计] {requirement.title}",
            content=self._format_design_doc(
                requirement, analysis, architecture, api_design,
                database_changes, dependencies
            ),
            architecture=architecture,
            api_design=api_design,
            database_changes=database_changes,
            dependencies=dependencies,
            implementation_phases=implementation_phases,
            non_functional_requirements=non_functional_requirements,
            impact_analysis=impact,
            affected_files=self._predict_affected_files(analysis),
            status=SolutionStatus.DRAFT,
            created_by_agent=self.AGENT_NAME,
        )

        return solution

    def _format_design_doc(
        self,
        requirement: Requirement,
        analysis: Dict[str, Any],
        architecture: List[ArchitectureComponent],
        api_design: List[APIEndpoint],
        database_changes: List[DatabaseChange],
        dependencies: List[str],
    ) -> str:
        """格式化设计文档"""
        content = f"""## 功能设计文档

### 需求概述
{requirement.description}

### 需求分析
- **功能类型**: {', '.join(analysis['feature_types'])}
- **复杂度**: {analysis['complexity']}
- **识别的实体**: {', '.join(analysis['entities']) if analysis['entities'] else '待定义'}
- **分析置信度**: {analysis['confidence']:.0%}

### 架构设计
"""
        for comp in architecture:
            content += f"""
#### {comp.name}
- **类型**: {comp.type}
- **描述**: {comp.description}
- **依赖**: {', '.join(comp.dependencies) if comp.dependencies else '无'}
- **接口**: {', '.join(comp.interfaces) if comp.interfaces else '无'}
"""

        content += "\n### API 设计\n"
        for endpoint in api_design:
            content += f"""
#### {endpoint.method} {endpoint.path}
- **描述**: {endpoint.description}
"""
            if endpoint.request_body:
                content += f"- **请求体**: `{endpoint.request_body}`\n"
            if endpoint.response_body:
                content += f"- **响应体**: `{endpoint.response_body}`\n"

        if database_changes:
            content += "\n### 数据库设计\n"
            for change in database_changes:
                content += f"""
#### {change.change_type}: {change.table_name}
- **描述**: {change.description}
"""

        if dependencies:
            content += "\n### 依赖项\n"
            for dep in dependencies:
                content += f"- {dep}\n"

        return content

    def _estimate_impact(
        self, requirement: Requirement, analysis: Dict[str, Any]
    ) -> ImpactAnalysis:
        """评估影响"""
        complexity = analysis.get("complexity", "medium")

        level_map = {
            "high": ImpactLevel.HIGH,
            "medium": ImpactLevel.MEDIUM,
            "low": ImpactLevel.LOW,
        }
        impact_level = level_map.get(complexity, ImpactLevel.MEDIUM)

        feature_types = analysis.get("feature_types", [])
        affected_modules = []

        module_mapping = {
            "crud": ["数据访问层", "业务逻辑层", "API 层"],
            "authentication": ["认证模块", "用户模块"],
            "file_upload": ["文件服务", "存储服务"],
            "notification": ["通知服务", "消息队列"],
            "search": ["搜索服务", "索引服务"],
            "report": ["报表服务", "数据分析层"],
        }

        for ft in feature_types:
            if ft in module_mapping:
                affected_modules.extend(module_mapping[ft])

        affected_modules = list(set(affected_modules))

        return ImpactAnalysis(
            level=impact_level,
            scope=f"新增功能涉及 {len(affected_modules)} 个模块",
            affected_modules=affected_modules,
            affected_services=[],
            risk_points=["新功能需要充分测试", "可能需要数据库迁移"],
            mitigation_strategies=["分阶段发布", "准备回滚方案", "完善监控告警"],
        )

    def _identify_dependencies(self, analysis: Dict[str, Any]) -> List[str]:
        """识别依赖项"""
        dependencies = []
        feature_types = analysis.get("feature_types", [])

        dependency_mapping = {
            "authentication": ["pyjwt", "passlib", "python-jose"],
            "file_upload": ["python-multipart", "boto3"],
            "notification": ["celery", "redis", "email-validator"],
            "search": ["elasticsearch", "whoosh"],
            "report": ["pandas", "openpyxl", "matplotlib"],
            "scheduling": ["celery", "redis", "croniter"],
        }

        for ft in feature_types:
            if ft in dependency_mapping:
                dependencies.extend(dependency_mapping[ft])

        return list(set(dependencies))

    def _plan_implementation_phases(self, analysis: Dict[str, Any]) -> List[str]:
        """规划实现阶段"""
        complexity = analysis.get("complexity", "medium")

        if complexity == "high":
            return [
                "Phase 1: 基础架构搭建和数据模型设计",
                "Phase 2: 核心业务逻辑实现",
                "Phase 3: API 接口开发和集成",
                "Phase 4: 测试和性能优化",
                "Phase 5: 文档编写和上线准备",
            ]
        elif complexity == "medium":
            return [
                "Phase 1: 数据模型和 API 设计",
                "Phase 2: 核心功能实现",
                "Phase 3: 测试和优化",
            ]
        else:
            return [
                "Phase 1: 功能实现",
                "Phase 2: 测试和发布",
            ]

    def _define_nfr(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """定义非功能需求"""
        nfr = {
            "性能": "API 响应时间 < 500ms (P95)",
            "可用性": "服务可用性 > 99.9%",
            "安全性": "所有 API 需要认证，敏感数据加密存储",
        }

        feature_types = analysis.get("feature_types", [])

        if "authentication" in feature_types:
            nfr["认证"] = "支持 JWT Token，过期时间可配置"

        if "file_upload" in feature_types:
            nfr["文件"] = "单文件大小限制 10MB，支持常见格式"

        if "search" in feature_types:
            nfr["搜索"] = "搜索延迟 < 200ms，支持模糊匹配"

        return nfr

    def _predict_affected_files(self, analysis: Dict[str, Any]) -> List[str]:
        """预测受影响的文件"""
        files = []
        entities = analysis.get("entities", ["resource"])
        entity = entities[0] if entities else "resource"

        files.extend([
            f"models/{entity}.py",
            f"services/{entity}_service.py",
            f"api/routes/{entity}s.py",
        ])

        feature_types = analysis.get("feature_types", [])
        if "authentication" in feature_types:
            files.extend(["middleware/auth.py", "utils/jwt.py"])

        if "file_upload" in feature_types:
            files.extend(["services/file_service.py", "utils/storage.py"])

        return files


feature_agent_service = FeatureDesignAgentService()
