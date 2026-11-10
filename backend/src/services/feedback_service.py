"""知识反馈服务

负责闭环知识管理，包括：
- 记录完成结果
- 更新知识库
- 创建案例
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .requirement_service import RequirementService
    from .solution_service import SolutionService
    from .knowledge_service import KnowledgeService
    from .codegen_service import CodeGenService
    from .test_service import TestService


class CompletionRecord(BaseModel):
    """完成记录模型"""
    id: UUID = Field(default_factory=uuid4, description="记录 ID")
    requirement_id: UUID = Field(..., description="需求 ID")
    solution_id: Optional[UUID] = Field(None, description="方案 ID")
    codegen_task_id: Optional[UUID] = Field(None, description="代码生成任务 ID")
    test_task_id: Optional[UUID] = Field(None, description="测试任务 ID")
    status: str = Field(default="completed", description="完成状态")
    success: bool = Field(default=True, description="是否成功")
    summary: str = Field(default="", description="完成摘要")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="指标数据")
    lessons_learned: List[str] = Field(default_factory=list, description="经验教训")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class CaseStudy(BaseModel):
    """案例模型"""
    id: UUID = Field(default_factory=uuid4, description="案例 ID")
    requirement_id: UUID = Field(..., description="需求 ID")
    title: str = Field(..., description="案例标题")
    description: str = Field(default="", description="案例描述")
    problem: str = Field(default="", description="问题描述")
    solution_summary: str = Field(default="", description="解决方案摘要")
    implementation: str = Field(default="", description="实现细节")
    results: str = Field(default="", description="结果")
    tags: List[str] = Field(default_factory=list, description="标签")
    related_documents: List[UUID] = Field(default_factory=list, description="相关文档")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class KnowledgeUpdate(BaseModel):
    """知识更新记录"""
    id: UUID = Field(default_factory=uuid4, description="更新 ID")
    knowledge_base_id: Optional[UUID] = Field(None, description="知识库 ID")
    document_id: Optional[UUID] = Field(None, description="文档 ID")
    update_type: str = Field(..., description="更新类型: create/update/link")
    content_summary: str = Field(default="", description="内容摘要")
    source_requirement_id: Optional[UUID] = Field(None, description="来源需求 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True


class FeedbackService:
    """知识反馈服务

    负责闭环知识管理：
    1. 记录需求完成结果
    2. 提取经验和教训
    3. 更新知识库
    4. 创建案例供后续参考
    """

    def __init__(self):
        self._completion_records: Dict[UUID, CompletionRecord] = {}
        self._case_studies: Dict[UUID, CaseStudy] = {}
        self._knowledge_updates: Dict[UUID, KnowledgeUpdate] = {}
        self._requirement_to_records: Dict[UUID, List[UUID]] = {}
        self._requirement_service: Optional["RequirementService"] = None
        self._solution_service: Optional["SolutionService"] = None
        self._knowledge_service: Optional["KnowledgeService"] = None
        self._codegen_service: Optional["CodeGenService"] = None
        self._test_service: Optional["TestService"] = None

    def set_requirement_service(self, requirement_service: "RequirementService"):
        """设置需求服务引用"""
        self._requirement_service = requirement_service

    def set_solution_service(self, solution_service: "SolutionService"):
        """设置方案服务引用"""
        self._solution_service = solution_service

    def set_knowledge_service(self, knowledge_service: "KnowledgeService"):
        """设置知识库服务引用"""
        self._knowledge_service = knowledge_service

    def set_codegen_service(self, codegen_service: "CodeGenService"):
        """设置代码生成服务引用"""
        self._codegen_service = codegen_service

    def set_test_service(self, test_service: "TestService"):
        """设置测试服务引用"""
        self._test_service = test_service

    def record_completion(
        self,
        requirement_id: UUID,
        result: Dict[str, Any],
    ) -> CompletionRecord:
        """记录完成结果

        Args:
            requirement_id: 需求 ID
            result: 完成结果数据

        Returns:
            CompletionRecord: 完成记录
        """
        success = result.get("success", True)
        summary = result.get("summary", "")

        metrics = {
            "total_duration_hours": result.get("duration_hours", 0),
            "code_files_generated": result.get("code_files", 0),
            "test_cases_passed": result.get("tests_passed", 0),
            "test_cases_failed": result.get("tests_failed", 0),
            "code_coverage_percent": result.get("coverage", 0),
            "lint_errors_fixed": result.get("lint_errors_fixed", 0),
        }

        lessons = self._extract_lessons_learned(requirement_id, result)

        record = CompletionRecord(
            requirement_id=requirement_id,
            solution_id=result.get("solution_id"),
            codegen_task_id=result.get("codegen_task_id"),
            test_task_id=result.get("test_task_id"),
            status="completed" if success else "failed",
            success=success,
            summary=summary,
            metrics=metrics,
            lessons_learned=lessons,
        )

        self._completion_records[record.id] = record

        if requirement_id not in self._requirement_to_records:
            self._requirement_to_records[requirement_id] = []
        self._requirement_to_records[requirement_id].append(record.id)

        if success:
            self._trigger_knowledge_update(record)

        return record

    def _extract_lessons_learned(
        self,
        requirement_id: UUID,
        result: Dict[str, Any],
    ) -> List[str]:
        """提取经验教训"""
        lessons = []

        if result.get("tests_failed", 0) > 0:
            lessons.append("部分测试用例失败，需要关注边界条件处理")

        if result.get("coverage", 0) < 80:
            lessons.append("代码覆盖率未达到 80%，建议补充测试用例")

        if result.get("lint_errors_fixed", 0) > 10:
            lessons.append("存在较多代码规范问题，建议加强代码审查")

        if result.get("iterations", 1) > 3:
            lessons.append("经过多次迭代才完成，需要优化需求分析流程")

        if result.get("duration_hours", 0) > 24:
            lessons.append("耗时超过预期，考虑拆分为更小的任务")

        custom_lessons = result.get("lessons", [])
        if custom_lessons:
            lessons.extend(custom_lessons)

        return lessons

    def _trigger_knowledge_update(self, record: CompletionRecord):
        """触发知识库更新"""
        update = KnowledgeUpdate(
            update_type="link",
            content_summary=f"完成记录已关联: {record.summary[:100]}",
            source_requirement_id=record.requirement_id,
        )
        self._knowledge_updates[update.id] = update

    def update_knowledge_base(
        self,
        requirement_id: UUID,
        solution_summary: str,
        code_summary: str,
    ) -> Optional[KnowledgeUpdate]:
        """更新知识库

        Args:
            requirement_id: 需求 ID
            solution_summary: 方案摘要
            code_summary: 代码摘要

        Returns:
            KnowledgeUpdate: 知识更新记录
        """
        if not self._knowledge_service:
            return None

        if not self._requirement_service:
            return None

        requirement = self._requirement_service.get(requirement_id)
        if not requirement:
            return None

        content = f"""# {requirement.title}

## 问题描述
{requirement.description}

## 解决方案
{solution_summary}

## 实现要点
{code_summary}

## 相关标签
- 类型: {requirement.type.value}
- 优先级: {requirement.priority.value}
"""

        kbs = self._knowledge_service.get_knowledge_bases(requirement.project_id)

        target_kb = None
        for kb in kbs:
            if kb.type.value == "faq":
                target_kb = kb
                break

        if not target_kb and kbs:
            target_kb = kbs[0]

        document_id = None
        if target_kb:
            from ..models.knowledge import DocumentCreate

            doc = self._knowledge_service.add_document(
                kb_id=target_kb.id,
                data=DocumentCreate(
                    title=f"案例: {requirement.title}",
                    content=content,
                    file_type="markdown",
                ),
            )
            if doc:
                document_id = doc.id

        update = KnowledgeUpdate(
            knowledge_base_id=target_kb.id if target_kb else None,
            document_id=document_id,
            update_type="create",
            content_summary=f"创建案例文档: {requirement.title}",
            source_requirement_id=requirement_id,
        )

        self._knowledge_updates[update.id] = update

        return update

    def create_case_study(self, requirement_id: UUID) -> Optional[CaseStudy]:
        """创建案例

        Args:
            requirement_id: 需求 ID

        Returns:
            CaseStudy: 创建的案例
        """
        if not self._requirement_service:
            return None

        requirement = self._requirement_service.get(requirement_id)
        if not requirement:
            return None

        solution = None
        solution_summary = ""
        if self._solution_service:
            solutions = self._solution_service.get_solutions_by_requirement(requirement_id)
            if solutions:
                solution = solutions[0]
                solution_summary = solution.description

        implementation = ""
        if self._codegen_service and solution:
            tasks = self._codegen_service.get_tasks_by_solution(solution.id)
            if tasks:
                codegen_task = tasks[0]
                file_list = [f.path for f in codegen_task.files]
                implementation = f"生成了 {len(file_list)} 个文件: {', '.join(file_list[:5])}"
                if len(file_list) > 5:
                    implementation += f" 等"

        results = ""
        if self._test_service:
            test_stats = self._test_service.get_statistics()
            results = f"测试通过率: {test_stats['tests']['passed']}/{test_stats['tests']['total']}"

        tags = self._generate_tags(requirement, solution)

        case = CaseStudy(
            requirement_id=requirement_id,
            title=f"案例: {requirement.title}",
            description=f"基于需求 '{requirement.title}' 的完整实现案例",
            problem=requirement.description,
            solution_summary=solution_summary,
            implementation=implementation,
            results=results,
            tags=tags,
        )

        self._case_studies[case.id] = case

        return case

    def _generate_tags(self, requirement, solution) -> List[str]:
        """生成标签"""
        tags = []

        if requirement:
            tags.append(f"type:{requirement.type.value}")
            tags.append(f"priority:{requirement.priority.value}")

        if solution:
            tags.append(f"solution:{solution.type.value}")

        return tags

    def get_completion_record(self, record_id: UUID) -> Optional[CompletionRecord]:
        """获取完成记录"""
        return self._completion_records.get(record_id)

    def get_completion_records_by_requirement(
        self,
        requirement_id: UUID,
    ) -> List[CompletionRecord]:
        """获取需求的完成记录列表"""
        record_ids = self._requirement_to_records.get(requirement_id, [])
        return [
            self._completion_records[rid]
            for rid in record_ids
            if rid in self._completion_records
        ]

    def get_case_study(self, case_id: UUID) -> Optional[CaseStudy]:
        """获取案例"""
        return self._case_studies.get(case_id)

    def get_case_studies_by_requirement(
        self,
        requirement_id: UUID,
    ) -> List[CaseStudy]:
        """获取需求的案例列表"""
        return [
            case for case in self._case_studies.values()
            if case.requirement_id == requirement_id
        ]

    def list_case_studies(
        self,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[CaseStudy]:
        """列出案例

        Args:
            tags: 标签过滤
            page: 页码
            page_size: 每页数量

        Returns:
            List[CaseStudy]: 案例列表
        """
        cases = list(self._case_studies.values())

        if tags:
            cases = [
                c for c in cases
                if any(tag in c.tags for tag in tags)
            ]

        cases.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return cases[start:end]

    def search_similar_cases(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[CaseStudy]:
        """搜索相似案例

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            List[CaseStudy]: 相似案例列表
        """
        cases = list(self._case_studies.values())

        query_lower = query.lower()
        scored_cases = []

        for case in cases:
            score = 0.0

            if query_lower in case.title.lower():
                score += 0.5

            if query_lower in case.problem.lower():
                score += 0.3

            if query_lower in case.solution_summary.lower():
                score += 0.2

            for tag in case.tags:
                if query_lower in tag.lower():
                    score += 0.1

            if score > 0:
                scored_cases.append((case, score))

        scored_cases.sort(key=lambda x: x[1], reverse=True)

        return [case for case, _ in scored_cases[:top_k]]

    def get_knowledge_update(self, update_id: UUID) -> Optional[KnowledgeUpdate]:
        """获取知识更新记录"""
        return self._knowledge_updates.get(update_id)

    def list_knowledge_updates(
        self,
        requirement_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[KnowledgeUpdate]:
        """列出知识更新记录"""
        updates = list(self._knowledge_updates.values())

        if requirement_id:
            updates = [
                u for u in updates
                if u.source_requirement_id == requirement_id
            ]

        updates.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return updates[start:end]

    def get_statistics(self) -> Dict[str, Any]:
        """获取反馈统计

        Returns:
            Dict: 统计数据
        """
        records = list(self._completion_records.values())
        cases = list(self._case_studies.values())
        updates = list(self._knowledge_updates.values())

        successful_records = [r for r in records if r.success]
        failed_records = [r for r in records if not r.success]

        all_lessons = []
        for record in records:
            all_lessons.extend(record.lessons_learned)

        lesson_counts: Dict[str, int] = {}
        for lesson in all_lessons:
            lesson_counts[lesson] = lesson_counts.get(lesson, 0) + 1

        top_lessons = sorted(
            lesson_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return {
            "completion_records": {
                "total": len(records),
                "successful": len(successful_records),
                "failed": len(failed_records),
            },
            "case_studies": {
                "total": len(cases),
            },
            "knowledge_updates": {
                "total": len(updates),
                "by_type": {
                    "create": len([u for u in updates if u.update_type == "create"]),
                    "update": len([u for u in updates if u.update_type == "update"]),
                    "link": len([u for u in updates if u.update_type == "link"]),
                },
            },
            "top_lessons_learned": [
                {"lesson": lesson, "count": count}
                for lesson, count in top_lessons
            ],
        }


feedback_service = FeedbackService()
