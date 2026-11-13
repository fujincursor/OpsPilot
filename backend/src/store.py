"""把业务对象写入关系表，并在启动时从空库读回。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .schema import (
    AgentPromptTemplateRow,
    AgentRow,
    AgentSkillRow,
    CaseDocumentRow,
    CaseStudyRow,
    CaseTagRow,
    ChatMessageRow,
    ChatSessionRow,
    CiPipelineRow,
    CiStageRow,
    CodeFileRow,
    CodegenAppliedPathRow,
    CodegenLocationRow,
    CodegenStepRow,
    CodegenTaskRow,
    CompletionLessonRow,
    CompletionRecordRow,
    DocumentRow,
    KnowledgeBaseRow,
    KnowledgeIndexJobRow,
    KnowledgeIndexPathRow,
    KnowledgeUpdateRow,
    NotificationRow,
    ProjectMemberRow,
    ProjectProfileRow,
    ProjectRow,
    ProjectSkillRow,
    RequirementKeywordRow,
    RequirementRow,
    ReviewCommentRow,
    ReviewDecisionRow,
    ReviewHistoryRow,
    ReviewItemRow,
    SandboxAllowedDomainRow,
    SandboxSettingsRow,
    SandboxSystemToolRow,
    SkillCatalogRow,
    SolutionApiEndpointRow,
    SolutionComponentRefRow,
    SolutionComponentRow,
    SolutionDatabaseChangeRow,
    SolutionNfrRow,
    SolutionRow,
    SolutionTextItemRow,
    TestCaseRow,
    TestReportFailureRow,
    TestReportRow,
    TestResultRow,
    TestTaskRow,
    UserRow,
)

_engine = None


def bind(engine) -> None:
    global _engine
    _engine = engine


def session() -> Session:
    return Session(_engine)


def _dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "")
    return datetime.fromisoformat(text)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else None, ensure_ascii=False)


def _load_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    return json.loads(value)


def _enum(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value


def load_all(collection: str, model, loader, key_type) -> list[tuple[Any, Any]]:
    with session() as db:
        rows = _load_rows(db, collection)
    items = []
    for key, payload in rows:
        parsed = key_type(key)
        if loader is not None:
            value = loader(payload)
        elif model is not None:
            value = model.model_validate(payload)
        else:
            value = payload
        items.append((parsed, value))
    return items


def save(collection: str, key: Any, value: Any) -> None:
    payload = _dump(value)
    with session() as db:
        _save_row(db, collection, str(key), payload if not isinstance(payload, list) else payload)
        db.commit()


def remove(collection: str, key: Any) -> None:
    with session() as db:
        _delete_row(db, collection, str(key))
        db.commit()


def _texts(db: Session, solution_id: str, kind: str) -> list[str]:
    rows = db.scalars(
        select(SolutionTextItemRow)
        .where(SolutionTextItemRow.solution_id == solution_id, SolutionTextItemRow.item_kind == kind)
        .order_by(SolutionTextItemRow.position)
    ).all()
    return [row.value for row in rows]


def _write_texts(db: Session, solution_id: str, kind: str, values: list[str]) -> None:
    for index, value in enumerate(values or []):
        db.add(SolutionTextItemRow(solution_id=solution_id, item_kind=kind, value=value, position=index))


def _load_rows(db: Session, collection: str) -> list[tuple[str, Any]]:
    if collection == "users":
        return [(row.id, _user_payload(row)) for row in db.scalars(select(UserRow)).all()]
    if collection == "projects":
        return [(row.id, _project_payload(db, row)) for row in db.scalars(select(ProjectRow)).all()]
    if collection == "requirements":
        return [(row.id, _requirement_payload(db, row)) for row in db.scalars(select(RequirementRow)).all()]
    if collection == "solutions":
        return [(row.id, _solution_payload(db, row)) for row in db.scalars(select(SolutionRow)).all()]
    if collection == "codegen_tasks":
        return [(row.id, _codegen_payload(db, row)) for row in db.scalars(select(CodegenTaskRow)).all()]
    if collection == "test_tasks":
        return [(row.id, _test_task_payload(db, row)) for row in db.scalars(select(TestTaskRow)).all()]
    if collection == "test_reports":
        return [(row.task_id, _test_report_payload(db, row)) for row in db.scalars(select(TestReportRow)).all()]
    if collection == "ci_pipelines":
        return [(row.id, _ci_payload(db, row)) for row in db.scalars(select(CiPipelineRow)).all()]
    if collection == "review_items":
        return [(row.id, _review_payload(db, row)) for row in db.scalars(select(ReviewItemRow)).all()]
    if collection == "review_history":
        grouped: dict[str, list] = {}
        rows = db.scalars(select(ReviewHistoryRow).order_by(ReviewHistoryRow.position)).all()
        for row in rows:
            grouped.setdefault(row.review_item_id, []).append({
                "id": row.id,
                "action": row.action,
                "actor": row.actor,
                "details": row.details,
                "created_at": row.created_at,
            })
        return list(grouped.items())
    if collection == "notifications":
        return [(row.id, _notification_payload(row)) for row in db.scalars(select(NotificationRow)).all()]
    if collection == "chat_sessions":
        return [(row.id, _chat_payload(db, row)) for row in db.scalars(select(ChatSessionRow)).all()]
    if collection == "knowledge_bases":
        return [(row.id, _kb_payload(db, row)) for row in db.scalars(select(KnowledgeBaseRow)).all()]
    if collection == "documents":
        return [(row.id, _document_payload(row)) for row in db.scalars(select(DocumentRow)).all()]
    if collection == "agents":
        return [(row.id, _agent_payload(db, row)) for row in db.scalars(select(AgentRow)).all()]
    if collection == "completion_records":
        return [(row.id, _completion_payload(db, row)) for row in db.scalars(select(CompletionRecordRow)).all()]
    if collection == "case_studies":
        return [(row.id, _case_payload(db, row)) for row in db.scalars(select(CaseStudyRow)).all()]
    if collection == "knowledge_updates":
        return [(row.id, _knowledge_update_payload(row)) for row in db.scalars(select(KnowledgeUpdateRow)).all()]
    return []


def _save_row(db: Session, collection: str, key: str, payload: Any) -> None:
    _delete_row(db, collection, key)
    if collection == "users":
        db.add(UserRow(
            id=key, username=payload["username"], email=payload["email"], role=_enum(payload["role"]),
            hashed_password=payload["hashed_password"], is_active=payload.get("is_active", True),
            created_at=_dt(payload["created_at"]), updated_at=_dt(payload.get("updated_at")),
        ))
    elif collection == "projects":
        _save_project(db, key, payload)
    elif collection == "requirements":
        _save_requirement(db, key, payload)
    elif collection == "solutions":
        _save_solution(db, key, payload)
    elif collection == "codegen_tasks":
        _save_codegen(db, key, payload)
    elif collection == "test_tasks":
        _save_test_task(db, key, payload)
    elif collection == "test_reports":
        _save_test_report(db, key, payload)
    elif collection == "ci_pipelines":
        _save_ci(db, key, payload)
    elif collection == "review_items":
        _save_review(db, key, payload)
    elif collection == "review_history":
        for index, item in enumerate(payload or []):
            db.add(ReviewHistoryRow(
                id=str(item["id"]), review_item_id=key, action=item["action"], actor=item["actor"],
                details=item.get("details") or "", created_at=_dt(item["created_at"]), position=index,
            ))
    elif collection == "notifications":
        db.add(NotificationRow(
            id=key, user_id=payload["user_id"], type=_enum(payload["type"]), title=payload["title"],
            content=payload.get("content") or "", review_item_id=_text(payload.get("review_item_id")) or None,
            is_read=bool(payload.get("is_read", False)), created_at=_dt(payload["created_at"]),
        ))
    elif collection == "chat_sessions":
        _save_chat(db, key, payload)
    elif collection == "knowledge_bases":
        _save_kb(db, key, payload)
    elif collection == "documents":
        db.add(DocumentRow(
            id=key, knowledge_base_id=str(payload["knowledge_base_id"]), title=payload["title"],
            content=payload.get("content"), file_path=payload.get("file_path"), file_type=payload.get("file_type"),
            embedding_status=_enum(payload.get("embedding_status") or "pending"),
            embedding_model=payload.get("embedding_model"), chunk_count=int(payload.get("chunk_count") or 0),
            error_message=payload.get("error_message"), created_at=_dt(payload["created_at"]),
        ))
    elif collection == "agents":
        _save_agent(db, key, payload)
    elif collection == "completion_records":
        _save_completion(db, key, payload)
    elif collection == "case_studies":
        _save_case(db, key, payload)
    elif collection == "knowledge_updates":
        db.add(KnowledgeUpdateRow(
            id=key, knowledge_base_id=_text(payload.get("knowledge_base_id")) or None,
            document_id=_text(payload.get("document_id")) or None, update_type=payload["update_type"],
            content_summary=payload.get("content_summary") or "",
            source_requirement_id=_text(payload.get("source_requirement_id")) or None,
            created_at=_dt(payload["created_at"]),
        ))


def _delete_row(db: Session, collection: str, key: str) -> None:
    mapping = {
        "users": UserRow,
        "projects": ProjectRow,
        "requirements": RequirementRow,
        "solutions": SolutionRow,
        "codegen_tasks": CodegenTaskRow,
        "test_tasks": TestTaskRow,
        "ci_pipelines": CiPipelineRow,
        "review_items": ReviewItemRow,
        "notifications": NotificationRow,
        "chat_sessions": ChatSessionRow,
        "knowledge_bases": KnowledgeBaseRow,
        "documents": DocumentRow,
        "agents": AgentRow,
        "completion_records": CompletionRecordRow,
        "case_studies": CaseStudyRow,
        "knowledge_updates": KnowledgeUpdateRow,
    }
    if collection == "test_reports":
        db.execute(delete(TestReportRow).where(TestReportRow.task_id == key))
        return
    if collection == "review_history":
        db.execute(delete(ReviewHistoryRow).where(ReviewHistoryRow.review_item_id == key))
        return
    model = mapping.get(collection)
    if model is not None:
        db.execute(delete(model).where(model.id == key))


def _save_project(db: Session, key: str, payload: dict) -> None:
    db.add(ProjectRow(
        id=key, name=payload["name"], description=payload.get("description"), repo_url=payload.get("repo_url"),
        status=_enum(payload.get("status") or "active"), prompt_template=payload.get("prompt_template") or "",
        toolchain=payload.get("toolchain") or "", code_origin=payload.get("code_origin") or "none",
        code_status=payload.get("code_status") or "empty", code_branch=payload.get("code_branch") or "",
        code_revision=payload.get("code_revision") or "", code_message=payload.get("code_message") or "",
        code_updated_at=_dt(payload.get("code_updated_at")), created_at=_dt(payload["created_at"]),
        updated_at=_dt(payload["updated_at"]),
    ))
    db.flush()
    profile = payload.get("profile") or {}
    db.add(ProjectProfileRow(
        project_id=key, overview=profile.get("overview") or "", architecture=profile.get("architecture") or "",
        directory_layout=profile.get("directory_layout") or "", key_modules=profile.get("key_modules") or "",
        config_notes=profile.get("config_notes") or "", runbook=profile.get("runbook") or "",
    ))
    sandbox = payload.get("sandbox") or {}
    db.add(SandboxSettingsRow(
        project_id=key, backend=sandbox.get("backend") or "local", image=sandbox.get("image") or "python:3.11-slim",
        memory_mb=int(sandbox.get("memory_mb") or 512), cpu=float(sandbox.get("cpu") or 1),
        timeout_seconds=int(sandbox.get("timeout_seconds") or 300), disk_gb=int(sandbox.get("disk_gb") or 10),
        network_policy=sandbox.get("network_policy") or "disabled",
        python_requirements=sandbox.get("python_requirements") or "",
        run_as_non_root=bool(sandbox.get("run_as_non_root", True)),
        disable_privileged=bool(sandbox.get("disable_privileged", True)),
        read_only_root=bool(sandbox.get("read_only_root", True)),
        disable_setuid=bool(sandbox.get("disable_setuid", True)),
        seccomp=bool(sandbox.get("seccomp", False)),
        kubeconfig_mode=sandbox.get("kubeconfig_mode") or "default",
        kubeconfig=sandbox.get("kubeconfig") or "", namespace=sandbox.get("namespace") or "",
        service_account=sandbox.get("service_account") or "", e2b_api_key=sandbox.get("e2b_api_key") or "",
        e2b_template=sandbox.get("e2b_template") or "python-3.11",
    ))
    for index, domain in enumerate(sandbox.get("allowed_domains") or []):
        db.add(SandboxAllowedDomainRow(project_id=key, domain=domain, position=index))
    for index, tool in enumerate(sandbox.get("system_tools") or []):
        db.add(SandboxSystemToolRow(project_id=key, tool_name=tool, position=index))
    for member in payload.get("members") or []:
        db.add(ProjectMemberRow(project_id=key, username=member["username"], role=member.get("role") or "developer"))
    for skill in payload.get("skills") or []:
        db.add(ProjectSkillRow(
            project_id=key, skill_key=skill["key"], name=skill["name"], description=skill.get("description") or "",
            agent=skill.get("agent") or "", enabled=bool(skill.get("enabled", True)),
            usage_count=int(skill.get("usage_count") or 0),
        ))


def _project_payload(db: Session, row: ProjectRow) -> dict:
    profile = db.get(ProjectProfileRow, row.id)
    sandbox = db.get(SandboxSettingsRow, row.id)
    domains = db.scalars(select(SandboxAllowedDomainRow).where(SandboxAllowedDomainRow.project_id == row.id).order_by(SandboxAllowedDomainRow.position)).all()
    tools = db.scalars(select(SandboxSystemToolRow).where(SandboxSystemToolRow.project_id == row.id).order_by(SandboxSystemToolRow.position)).all()
    members = db.scalars(select(ProjectMemberRow).where(ProjectMemberRow.project_id == row.id)).all()
    skills = db.scalars(select(ProjectSkillRow).where(ProjectSkillRow.project_id == row.id)).all()
    return {
        "id": row.id, "name": row.name, "description": row.description, "repo_url": row.repo_url,
        "status": row.status, "prompt_template": row.prompt_template, "toolchain": row.toolchain,
        "code_origin": row.code_origin, "code_status": row.code_status, "code_branch": row.code_branch,
        "code_revision": row.code_revision, "code_message": row.code_message, "code_updated_at": row.code_updated_at,
        "created_at": row.created_at, "updated_at": row.updated_at,
        "profile": {
            "overview": profile.overview if profile else "",
            "architecture": profile.architecture if profile else "",
            "directory_layout": profile.directory_layout if profile else "",
            "key_modules": profile.key_modules if profile else "",
            "config_notes": profile.config_notes if profile else "",
            "runbook": profile.runbook if profile else "",
        },
        "sandbox": {
            "backend": sandbox.backend if sandbox else "local",
            "image": sandbox.image if sandbox else "python:3.11-slim",
            "memory_mb": sandbox.memory_mb if sandbox else 512,
            "cpu": sandbox.cpu if sandbox else 1,
            "timeout_seconds": sandbox.timeout_seconds if sandbox else 300,
            "disk_gb": sandbox.disk_gb if sandbox else 10,
            "network_policy": sandbox.network_policy if sandbox else "disabled",
            "python_requirements": sandbox.python_requirements if sandbox else "",
            "run_as_non_root": sandbox.run_as_non_root if sandbox else True,
            "disable_privileged": sandbox.disable_privileged if sandbox else True,
            "read_only_root": sandbox.read_only_root if sandbox else True,
            "disable_setuid": sandbox.disable_setuid if sandbox else True,
            "seccomp": sandbox.seccomp if sandbox else False,
            "kubeconfig_mode": sandbox.kubeconfig_mode if sandbox else "default",
            "kubeconfig": sandbox.kubeconfig if sandbox else "",
            "namespace": sandbox.namespace if sandbox else "",
            "service_account": sandbox.service_account if sandbox else "",
            "e2b_api_key": sandbox.e2b_api_key if sandbox else "",
            "e2b_template": sandbox.e2b_template if sandbox else "python-3.11",
            "allowed_domains": [item.domain for item in domains],
            "system_tools": [item.tool_name for item in tools],
        },
        "members": [{"username": item.username, "role": item.role} for item in members],
        "skills": [{
            "key": item.skill_key, "name": item.name, "description": item.description,
            "agent": item.agent, "enabled": item.enabled, "usage_count": item.usage_count,
        } for item in skills],
    }


def _user_payload(row: UserRow) -> dict:
    return {
        "id": row.id, "username": row.username, "email": row.email, "role": row.role,
        "hashed_password": row.hashed_password, "is_active": row.is_active,
        "created_at": row.created_at, "updated_at": row.updated_at,
    }


def _save_requirement(db: Session, key: str, payload: dict) -> None:
    db.add(RequirementRow(
        id=key, project_id=str(payload["project_id"]), title=payload["title"], description=payload["description"],
        source=_enum(payload.get("source") or "web"), type=_enum(payload.get("type") or "feature"),
        priority=_enum(payload.get("priority") or "medium"), status=_enum(payload.get("status") or "pending"),
        assignee=payload.get("assignee"), created_by=payload.get("created_by"),
        analysis_confidence=float(payload.get("analysis_confidence") or 0),
        session_id=_text(payload.get("session_id")) or None, auto_advance=bool(payload.get("auto_advance", True)),
        rework_count=int(payload.get("rework_count") or 0), failure_reason=payload.get("failure_reason"),
        created_at=_dt(payload["created_at"]), updated_at=_dt(payload["updated_at"]),
    ))
    db.flush()
    for index, keyword in enumerate(payload.get("keywords") or []):
        db.add(RequirementKeywordRow(requirement_id=key, keyword=keyword, position=index))


def _requirement_payload(db: Session, row: RequirementRow) -> dict:
    keywords = db.scalars(select(RequirementKeywordRow).where(RequirementKeywordRow.requirement_id == row.id).order_by(RequirementKeywordRow.position)).all()
    return {
        "id": row.id, "project_id": row.project_id, "title": row.title, "description": row.description,
        "source": row.source, "type": row.type, "priority": row.priority, "status": row.status,
        "assignee": row.assignee, "created_by": row.created_by, "analysis_confidence": row.analysis_confidence,
        "session_id": row.session_id, "auto_advance": row.auto_advance, "rework_count": row.rework_count,
        "failure_reason": row.failure_reason, "created_at": row.created_at, "updated_at": row.updated_at,
        "keywords": [item.keyword for item in keywords],
    }


def _save_solution(db: Session, key: str, payload: dict) -> None:
    impact = payload.get("impact_analysis") or {}
    db.add(SolutionRow(
        id=key, requirement_id=str(payload["requirement_id"]), title=payload["title"], content=payload["content"],
        type=_enum(payload["type"]), status=_enum(payload.get("status") or "draft"),
        impact_level=_enum(impact.get("level") or "medium"), impact_scope=impact.get("scope") or "",
        created_by_agent=payload.get("created_by_agent") or "", skill_key=payload.get("skill_key") or "",
        skill_name=payload.get("skill_name") or "", reviewed_by=payload.get("reviewed_by"),
        review_comment=payload.get("review_comment"), root_cause=payload.get("root_cause") or "",
        regression_risk=payload.get("regression_risk") or "", rollback_plan=payload.get("rollback_plan") or "",
        created_at=_dt(payload["created_at"]), updated_at=_dt(payload["updated_at"]),
    ))
    db.flush()
    _write_texts(db, key, "affected_file", payload.get("affected_files") or [])
    _write_texts(db, key, "fix_step", payload.get("fix_steps") or [])
    _write_texts(db, key, "test_suggestion", payload.get("test_cases") or [])
    _write_texts(db, key, "dependency", payload.get("dependencies") or [])
    _write_texts(db, key, "phase", payload.get("implementation_phases") or [])
    _write_texts(db, key, "impact_module", impact.get("affected_modules") or [])
    _write_texts(db, key, "impact_service", impact.get("affected_services") or [])
    _write_texts(db, key, "impact_risk", impact.get("risk_points") or [])
    _write_texts(db, key, "impact_mitigation", impact.get("mitigation_strategies") or [])
    for index, item in enumerate(payload.get("architecture") or []):
        component = SolutionComponentRow(
            solution_id=key, name=item["name"], component_type=item.get("type") or "",
            description=item.get("description") or "", position=index,
        )
        db.add(component)
        db.flush()
        for ref_index, value in enumerate(item.get("dependencies") or []):
            db.add(SolutionComponentRefRow(component_id=component.id, ref_kind="dependency", value=value, position=ref_index))
        for ref_index, value in enumerate(item.get("interfaces") or []):
            db.add(SolutionComponentRefRow(component_id=component.id, ref_kind="interface", value=value, position=ref_index))
    for index, item in enumerate(payload.get("api_design") or []):
        db.add(SolutionApiEndpointRow(
            solution_id=key, method=item["method"], path=item["path"], description=item.get("description") or "",
            request_body=_json(item.get("request_body")), response_body=_json(item.get("response_body")), position=index,
        ))
    for index, item in enumerate(payload.get("database_changes") or []):
        db.add(SolutionDatabaseChangeRow(
            solution_id=key, change_type=item["change_type"], table_name=item["table_name"],
            description=item.get("description") or "", sql_migration=item.get("sql_migration"), position=index,
        ))
    for name, value in (payload.get("non_functional_requirements") or {}).items():
        db.add(SolutionNfrRow(solution_id=key, name=name, value=value))


def _solution_payload(db: Session, row: SolutionRow) -> dict:
    components = db.scalars(select(SolutionComponentRow).where(SolutionComponentRow.solution_id == row.id).order_by(SolutionComponentRow.position)).all()
    architecture = []
    for component in components:
        refs = db.scalars(select(SolutionComponentRefRow).where(SolutionComponentRefRow.component_id == component.id).order_by(SolutionComponentRefRow.position)).all()
        architecture.append({
            "name": component.name, "type": component.component_type, "description": component.description,
            "dependencies": [item.value for item in refs if item.ref_kind == "dependency"],
            "interfaces": [item.value for item in refs if item.ref_kind == "interface"],
        })
    endpoints = db.scalars(select(SolutionApiEndpointRow).where(SolutionApiEndpointRow.solution_id == row.id).order_by(SolutionApiEndpointRow.position)).all()
    changes = db.scalars(select(SolutionDatabaseChangeRow).where(SolutionDatabaseChangeRow.solution_id == row.id).order_by(SolutionDatabaseChangeRow.position)).all()
    nfrs = db.scalars(select(SolutionNfrRow).where(SolutionNfrRow.solution_id == row.id)).all()
    return {
        "id": row.id, "requirement_id": row.requirement_id, "title": row.title, "content": row.content,
        "type": row.type, "status": row.status, "created_by_agent": row.created_by_agent,
        "skill_key": row.skill_key, "skill_name": row.skill_name, "reviewed_by": row.reviewed_by,
        "review_comment": row.review_comment, "root_cause": row.root_cause, "regression_risk": row.regression_risk,
        "rollback_plan": row.rollback_plan, "created_at": row.created_at, "updated_at": row.updated_at,
        "affected_files": _texts(db, row.id, "affected_file"),
        "fix_steps": _texts(db, row.id, "fix_step"),
        "test_cases": _texts(db, row.id, "test_suggestion"),
        "dependencies": _texts(db, row.id, "dependency"),
        "implementation_phases": _texts(db, row.id, "phase"),
        "impact_analysis": {
            "level": row.impact_level, "scope": row.impact_scope,
            "affected_modules": _texts(db, row.id, "impact_module"),
            "affected_services": _texts(db, row.id, "impact_service"),
            "risk_points": _texts(db, row.id, "impact_risk"),
            "mitigation_strategies": _texts(db, row.id, "impact_mitigation"),
        },
        "architecture": architecture,
        "api_design": [{
            "method": item.method, "path": item.path, "description": item.description,
            "request_body": _load_json(item.request_body, None), "response_body": _load_json(item.response_body, None),
        } for item in endpoints],
        "database_changes": [{
            "change_type": item.change_type, "table_name": item.table_name,
            "description": item.description, "sql_migration": item.sql_migration,
        } for item in changes],
        "non_functional_requirements": {item.name: item.value for item in nfrs},
    }


def _file_payload(row: CodeFileRow) -> dict:
    return {
        "path": row.path, "content": row.content, "language": row.language, "action": row.action,
        "diff": _load_json(row.diff_json, []),
    }


def _save_codegen(db: Session, key: str, payload: dict) -> None:
    db.add(CodegenTaskRow(
        id=key, solution_id=str(payload["solution_id"]), requirement_id=str(payload["requirement_id"]),
        status=_enum(payload.get("status") or "pending"), language=payload.get("language") or "python",
        error_message=payload.get("error_message"), sandbox_id=payload.get("sandbox_id"),
        sandbox_profile=payload.get("sandbox_profile"), lint_json=_json(payload.get("lint_result")),
        mr_json=_json(payload.get("mr_info")), applied_at=_dt(payload.get("applied_at")),
        created_at=_dt(payload["created_at"]), updated_at=_dt(payload["updated_at"]),
        completed_at=_dt(payload.get("completed_at")),
    ))
    db.flush()
    for index, item in enumerate(payload.get("files") or []):
        db.add(CodeFileRow(
            task_id=key, step_index=None, path=item["path"], content=item.get("content") or "",
            language=item.get("language") or "python", action=_enum(item.get("action") or "create"),
            diff_json=_json(item.get("diff") or []), position=index,
        ))
    for step in payload.get("steps") or []:
        db.add(CodegenStepRow(
            task_id=key, step_index=int(step["index"]), title=step["title"],
            status=_enum(step.get("status") or "pending"), output=step.get("output") or "",
            error_message=step.get("error_message"),
        ))
        for index, item in enumerate(step.get("files") or []):
            db.add(CodeFileRow(
                task_id=key, step_index=int(step["index"]), path=item["path"], content=item.get("content") or "",
                language=item.get("language") or "python", action=_enum(item.get("action") or "create"),
                diff_json=_json(item.get("diff") or []), position=index,
            ))
        for index, item in enumerate(step.get("locations") or []):
            db.add(CodegenLocationRow(
                task_id=key, step_index=int(step["index"]), path=item["path"], line=int(item.get("line") or 1),
                snippet=item.get("snippet") or "", reason=item.get("reason") or "", position=index,
            ))
    for index, path in enumerate(payload.get("applied_paths") or []):
        db.add(CodegenAppliedPathRow(task_id=key, path=path, position=index))


def _codegen_payload(db: Session, row: CodegenTaskRow) -> dict:
    files = db.scalars(select(CodeFileRow).where(CodeFileRow.task_id == row.id, CodeFileRow.step_index.is_(None)).order_by(CodeFileRow.position)).all()
    steps = db.scalars(select(CodegenStepRow).where(CodegenStepRow.task_id == row.id).order_by(CodegenStepRow.step_index)).all()
    applied = db.scalars(select(CodegenAppliedPathRow).where(CodegenAppliedPathRow.task_id == row.id).order_by(CodegenAppliedPathRow.position)).all()
    step_payloads = []
    for step in steps:
        step_files = db.scalars(select(CodeFileRow).where(CodeFileRow.task_id == row.id, CodeFileRow.step_index == step.step_index).order_by(CodeFileRow.position)).all()
        locations = db.scalars(select(CodegenLocationRow).where(CodegenLocationRow.task_id == row.id, CodegenLocationRow.step_index == step.step_index).order_by(CodegenLocationRow.position)).all()
        step_payloads.append({
            "index": step.step_index, "title": step.title, "status": step.status, "output": step.output,
            "error_message": step.error_message,
            "files": [_file_payload(item) for item in step_files],
            "locations": [{"path": item.path, "line": item.line, "snippet": item.snippet, "reason": item.reason} for item in locations],
        })
    return {
        "id": row.id, "solution_id": row.solution_id, "requirement_id": row.requirement_id,
        "status": row.status, "language": row.language, "error_message": row.error_message,
        "sandbox_id": row.sandbox_id, "sandbox_profile": row.sandbox_profile,
        "lint_result": _load_json(row.lint_json, None), "mr_info": _load_json(row.mr_json, None),
        "applied_at": row.applied_at, "created_at": row.created_at, "updated_at": row.updated_at,
        "completed_at": row.completed_at, "files": [_file_payload(item) for item in files],
        "steps": step_payloads, "applied_paths": [item.path for item in applied],
    }


def _save_test_task(db: Session, key: str, payload: dict) -> None:
    db.add(TestTaskRow(
        id=key, codegen_task_id=str(payload["codegen_task_id"]), requirement_id=str(payload["requirement_id"]),
        status=_enum(payload.get("status") or "pending"), error_message=payload.get("error_message"),
        sandbox_id=payload.get("sandbox_id"), sandbox_profile=payload.get("sandbox_profile"),
        coverage_json=_json(payload.get("coverage")), ci_pipeline_id=payload.get("ci_pipeline_id"),
        created_at=_dt(payload["created_at"]), updated_at=_dt(payload["updated_at"]),
        completed_at=_dt(payload.get("completed_at")),
    ))
    db.flush()
    for index, item in enumerate(payload.get("test_cases") or []):
        db.add(TestCaseRow(
            id=str(item["id"]), task_id=key, name=item["name"], description=item.get("description") or "",
            type=_enum(item.get("type") or "unit"), code=item.get("code") or "",
            expected_result=item.get("expected_result"), file_path=item.get("file_path") or "",
            target_function=item.get("target_function"), created_at=_dt(item["created_at"]), position=index,
        ))
    for index, item in enumerate(payload.get("results") or []):
        db.add(TestResultRow(
            task_id=key, test_case_id=str(item["test_case_id"]), status=_enum(item["status"]),
            actual_result=item.get("actual_result"), error_message=item.get("error_message"),
            stack_trace=item.get("stack_trace"), duration_ms=int(item.get("duration_ms") or 0),
            executed_at=_dt(item["executed_at"]), position=index,
        ))


def _test_task_payload(db: Session, row: TestTaskRow) -> dict:
    cases = db.scalars(select(TestCaseRow).where(TestCaseRow.task_id == row.id).order_by(TestCaseRow.position)).all()
    results = db.scalars(select(TestResultRow).where(TestResultRow.task_id == row.id).order_by(TestResultRow.position)).all()
    return {
        "id": row.id, "codegen_task_id": row.codegen_task_id, "requirement_id": row.requirement_id,
        "status": row.status, "error_message": row.error_message, "sandbox_id": row.sandbox_id,
        "sandbox_profile": row.sandbox_profile, "coverage": _load_json(row.coverage_json, None),
        "ci_pipeline_id": row.ci_pipeline_id, "created_at": row.created_at, "updated_at": row.updated_at,
        "completed_at": row.completed_at,
        "test_cases": [{
            "id": item.id, "name": item.name, "description": item.description, "type": item.type,
            "code": item.code, "expected_result": item.expected_result, "file_path": item.file_path,
            "target_function": item.target_function, "created_at": item.created_at,
        } for item in cases],
        "results": [{
            "test_case_id": item.test_case_id, "status": item.status, "actual_result": item.actual_result,
            "error_message": item.error_message, "stack_trace": item.stack_trace,
            "duration_ms": item.duration_ms, "executed_at": item.executed_at,
        } for item in results],
    }


def _save_test_report(db: Session, key: str, payload: dict) -> None:
    db.add(TestReportRow(
        task_id=key, total=int(payload.get("total") or 0), passed=int(payload.get("passed") or 0),
        failed=int(payload.get("failed") or 0), skipped=int(payload.get("skipped") or 0),
        coverage_percent=float(payload.get("coverage_percent") or 0),
        coverage_json=_json(payload.get("coverage_info")), duration_ms=int(payload.get("duration_ms") or 0),
        summary=payload.get("summary") or "", generated_at=_dt(payload["generated_at"]),
    ))
    db.flush()
    for index, name in enumerate(payload.get("failed_cases") or []):
        db.add(TestReportFailureRow(task_id=key, case_name=name, position=index))


def _test_report_payload(db: Session, row: TestReportRow) -> dict:
    names = db.scalars(select(TestReportFailureRow).where(TestReportFailureRow.task_id == row.task_id).order_by(TestReportFailureRow.position)).all()
    return {
        "task_id": row.task_id, "total": row.total, "passed": row.passed, "failed": row.failed,
        "skipped": row.skipped, "coverage_percent": row.coverage_percent,
        "coverage_info": _load_json(row.coverage_json, None), "duration_ms": row.duration_ms,
        "summary": row.summary, "generated_at": row.generated_at,
        "failed_cases": [item.case_name for item in names],
    }


def _save_ci(db: Session, key: str, payload: dict) -> None:
    db.add(CiPipelineRow(
        id=key, pipeline_id=payload["pipeline_id"], status=payload.get("status") or "pending",
        url=payload.get("url"), triggered_at=_dt(payload["triggered_at"]),
        completed_at=_dt(payload.get("completed_at")),
    ))
    db.flush()
    for index, stage in enumerate(payload.get("stages") or []):
        stage = stage if isinstance(stage, dict) else {"detail": str(stage)}
        db.add(CiStageRow(
            pipeline_row_id=key, name=str(stage.get("name") or ""), status=str(stage.get("status") or ""),
            detail=_json(stage), position=index,
        ))


def _ci_payload(db: Session, row: CiPipelineRow) -> dict:
    stages = db.scalars(select(CiStageRow).where(CiStageRow.pipeline_row_id == row.id).order_by(CiStageRow.position)).all()
    loaded = []
    for item in stages:
        parsed = _load_json(item.detail, None)
        if isinstance(parsed, dict):
            loaded.append(parsed)
        else:
            loaded.append({"name": item.name, "status": item.status, "detail": item.detail})
    return {
        "pipeline_id": row.pipeline_id, "status": row.status, "url": row.url,
        "triggered_at": row.triggered_at, "completed_at": row.completed_at,
        "stages": loaded,
    }


def _save_review(db: Session, key: str, payload: dict) -> None:
    db.add(ReviewItemRow(
        id=key, title=payload["title"], description=payload.get("description") or "",
        item_type=_enum(payload["item_type"]), item_id=str(payload["item_id"]),
        project_id=str(payload["project_id"]), requirement_id=_text(payload.get("requirement_id")) or None,
        session_id=_text(payload.get("session_id")) or None, status=_enum(payload.get("status") or "pending"),
        priority=_enum(payload.get("priority") or "medium"), reviewer=payload.get("reviewer"),
        created_at=_dt(payload["created_at"]), updated_at=_dt(payload["updated_at"]),
        due_at=_dt(payload.get("due_at")),
    ))
    db.flush()
    for index, item in enumerate(payload.get("comments") or []):
        db.add(ReviewCommentRow(
            id=str(item["id"]), review_item_id=key, author=item["author"], content=item["content"],
            created_at=_dt(item["created_at"]), position=index,
        ))
    for index, item in enumerate(payload.get("decisions") or []):
        db.add(ReviewDecisionRow(
            id=str(item["id"]), review_item_id=key, decision=_enum(item["decision"]), reviewer=item["reviewer"],
            reason=item.get("reason") or "", created_at=_dt(item["created_at"]), position=index,
        ))


def _review_payload(db: Session, row: ReviewItemRow) -> dict:
    comments = db.scalars(select(ReviewCommentRow).where(ReviewCommentRow.review_item_id == row.id).order_by(ReviewCommentRow.position)).all()
    decisions = db.scalars(select(ReviewDecisionRow).where(ReviewDecisionRow.review_item_id == row.id).order_by(ReviewDecisionRow.position)).all()
    return {
        "id": row.id, "title": row.title, "description": row.description, "item_type": row.item_type,
        "item_id": row.item_id, "project_id": row.project_id, "requirement_id": row.requirement_id,
        "session_id": row.session_id, "status": row.status, "priority": row.priority, "reviewer": row.reviewer,
        "created_at": row.created_at, "updated_at": row.updated_at, "due_at": row.due_at,
        "comments": [{"id": item.id, "review_item_id": item.review_item_id, "author": item.author, "content": item.content, "created_at": item.created_at} for item in comments],
        "decisions": [{"id": item.id, "review_item_id": item.review_item_id, "decision": item.decision, "reviewer": item.reviewer, "reason": item.reason, "created_at": item.created_at} for item in decisions],
    }


def _notification_payload(row: NotificationRow) -> dict:
    return {
        "id": row.id, "user_id": row.user_id, "type": row.type, "title": row.title, "content": row.content,
        "review_item_id": row.review_item_id, "is_read": row.is_read, "created_at": row.created_at,
    }


def _save_chat(db: Session, key: str, payload: dict) -> None:
    db.add(ChatSessionRow(
        id=key, project_id=str(payload["project_id"]), title=payload["title"],
        created_at=_dt(payload["created_at"]), updated_at=_dt(payload["updated_at"]),
    ))
    db.flush()
    for index, item in enumerate(payload.get("messages") or []):
        db.add(ChatMessageRow(
            id=str(item["id"]), session_id=key, role=item["role"], content=item.get("content") or "",
            sender=item.get("sender") or "", status=item.get("status"),
            knowledge_blocked=bool(item.get("knowledge_blocked", False)),
            knowledge_json=_json(item.get("knowledge_results") or []),
            classification_json=_json(item.get("classification")) if item.get("classification") else None,
            review_json=_json(item.get("review")) if item.get("review") else None,
            created_at=_dt(item["created_at"]), position=index,
        ))


def _chat_payload(db: Session, row: ChatSessionRow) -> dict:
    messages = db.scalars(select(ChatMessageRow).where(ChatMessageRow.session_id == row.id).order_by(ChatMessageRow.position)).all()
    return {
        "id": row.id, "project_id": row.project_id, "title": row.title,
        "created_at": row.created_at, "updated_at": row.updated_at,
        "messages": [{
            "id": item.id, "role": item.role, "content": item.content, "sender": item.sender,
            "status": item.status, "knowledge_blocked": item.knowledge_blocked,
            "knowledge_results": _load_json(item.knowledge_json, []),
            "classification": _load_json(item.classification_json, None),
            "review": _load_json(item.review_json, None), "created_at": item.created_at,
        } for item in messages],
    }


def _save_kb(db: Session, key: str, payload: dict) -> None:
    db.add(KnowledgeBaseRow(
        id=key, project_id=str(payload["project_id"]), name=payload["name"], description=payload.get("description"),
        type=_enum(payload.get("type") or "doc"), status=_enum(payload.get("status") or "pending"),
        document_count=int(payload.get("document_count") or 0),
        index_trigger=payload.get("index_trigger") or "manual",
        update_policy=payload.get("update_policy") or "incremental",
        created_at=_dt(payload["created_at"]), updated_at=_dt(payload["updated_at"]),
    ))
    db.flush()
    for index, path in enumerate(payload.get("index_paths") or []):
        db.add(KnowledgeIndexPathRow(knowledge_base_id=key, path=path, position=index))
    for index, job in enumerate(payload.get("index_jobs") or []):
        db.add(KnowledgeIndexJobRow(
            id=str(job["id"]), knowledge_base_id=key, status=job["status"], message=job.get("message") or "",
            created_at=_dt(job["created_at"]), position=index,
        ))


def _kb_payload(db: Session, row: KnowledgeBaseRow) -> dict:
    paths = db.scalars(select(KnowledgeIndexPathRow).where(KnowledgeIndexPathRow.knowledge_base_id == row.id).order_by(KnowledgeIndexPathRow.position)).all()
    jobs = db.scalars(select(KnowledgeIndexJobRow).where(KnowledgeIndexJobRow.knowledge_base_id == row.id).order_by(KnowledgeIndexJobRow.position)).all()
    return {
        "id": row.id, "project_id": row.project_id, "name": row.name, "description": row.description,
        "type": row.type, "status": row.status, "document_count": row.document_count,
        "index_trigger": row.index_trigger, "update_policy": row.update_policy,
        "created_at": row.created_at, "updated_at": row.updated_at,
        "index_paths": [item.path for item in paths],
        "index_jobs": [{"id": item.id, "status": item.status, "message": item.message, "created_at": item.created_at} for item in jobs],
    }


def _document_payload(row: DocumentRow) -> dict:
    return {
        "id": row.id, "knowledge_base_id": row.knowledge_base_id, "title": row.title, "content": row.content,
        "file_path": row.file_path, "file_type": row.file_type, "embedding_status": row.embedding_status,
        "embedding_model": row.embedding_model, "chunk_count": row.chunk_count,
        "error_message": row.error_message, "created_at": row.created_at,
    }


def _save_agent(db: Session, key: str, payload: dict) -> None:
    db.add(AgentRow(
        id=key, project_id=str(payload["project_id"]), name=payload["name"],
        agent_type=_enum(payload["agent_type"]), description=payload.get("description"),
        model_name=payload.get("model_name") or "deepseek-v4", temperature=float(payload.get("temperature") or 0.7),
        max_tokens=int(payload.get("max_tokens") or 4096), prompt=payload.get("prompt") or "",
        enabled=bool(payload.get("enabled", True)), created_at=_dt(payload["created_at"]),
        updated_at=_dt(payload["updated_at"]),
    ))
    db.flush()
    for index, skill in enumerate(payload.get("skills") or []):
        db.add(AgentSkillRow(agent_id=key, skill_key=skill, position=index))


def _agent_payload(db: Session, row: AgentRow) -> dict:
    skills = db.scalars(select(AgentSkillRow).where(AgentSkillRow.agent_id == row.id).order_by(AgentSkillRow.position)).all()
    return {
        "id": row.id, "project_id": row.project_id, "name": row.name, "agent_type": row.agent_type,
        "description": row.description, "model_name": row.model_name, "temperature": row.temperature,
        "max_tokens": row.max_tokens, "prompt": row.prompt, "enabled": row.enabled,
        "created_at": row.created_at, "updated_at": row.updated_at,
        "skills": [item.skill_key for item in skills],
    }


def _save_completion(db: Session, key: str, payload: dict) -> None:
    db.add(CompletionRecordRow(
        id=key, requirement_id=str(payload["requirement_id"]),
        solution_id=_text(payload.get("solution_id")) or None,
        codegen_task_id=_text(payload.get("codegen_task_id")) or None,
        test_task_id=_text(payload.get("test_task_id")) or None,
        status=payload.get("status") or "completed", success=bool(payload.get("success", True)),
        summary=payload.get("summary") or "", metrics_json=_json(payload.get("metrics") or {}),
        created_at=_dt(payload["created_at"]),
    ))
    db.flush()
    for index, lesson in enumerate(payload.get("lessons_learned") or []):
        db.add(CompletionLessonRow(record_id=key, lesson=lesson, position=index))


def _completion_payload(db: Session, row: CompletionRecordRow) -> dict:
    lessons = db.scalars(select(CompletionLessonRow).where(CompletionLessonRow.record_id == row.id).order_by(CompletionLessonRow.position)).all()
    return {
        "id": row.id, "requirement_id": row.requirement_id, "solution_id": row.solution_id,
        "codegen_task_id": row.codegen_task_id, "test_task_id": row.test_task_id, "status": row.status,
        "success": row.success, "summary": row.summary, "metrics": _load_json(row.metrics_json, {}),
        "lessons_learned": [item.lesson for item in lessons], "created_at": row.created_at,
    }


def _save_case(db: Session, key: str, payload: dict) -> None:
    db.add(CaseStudyRow(
        id=key, requirement_id=str(payload["requirement_id"]), title=payload["title"],
        description=payload.get("description") or "", problem=payload.get("problem") or "",
        solution_summary=payload.get("solution_summary") or "", implementation=payload.get("implementation") or "",
        results=payload.get("results") or "", created_at=_dt(payload["created_at"]),
    ))
    db.flush()
    for index, tag in enumerate(payload.get("tags") or []):
        db.add(CaseTagRow(case_id=key, tag=tag, position=index))
    for index, document_id in enumerate(payload.get("related_documents") or []):
        db.add(CaseDocumentRow(case_id=key, document_id=str(document_id), position=index))


def _case_payload(db: Session, row: CaseStudyRow) -> dict:
    tags = db.scalars(select(CaseTagRow).where(CaseTagRow.case_id == row.id).order_by(CaseTagRow.position)).all()
    documents = db.scalars(select(CaseDocumentRow).where(CaseDocumentRow.case_id == row.id).order_by(CaseDocumentRow.position)).all()
    return {
        "id": row.id, "requirement_id": row.requirement_id, "title": row.title, "description": row.description,
        "problem": row.problem, "solution_summary": row.solution_summary, "implementation": row.implementation,
        "results": row.results, "created_at": row.created_at,
        "tags": [item.tag for item in tags],
        "related_documents": [item.document_id for item in documents],
    }


def _knowledge_update_payload(row: KnowledgeUpdateRow) -> dict:
    return {
        "id": row.id, "knowledge_base_id": row.knowledge_base_id, "document_id": row.document_id,
        "update_type": row.update_type, "content_summary": row.content_summary,
        "source_requirement_id": row.source_requirement_id, "created_at": row.created_at,
    }


def list_skill_catalog() -> list[dict[str, str]]:
    with session() as db:
        rows = db.scalars(select(SkillCatalogRow)).all()
        return [
            {
                "key": row.skill_key,
                "name": row.name,
                "description": row.description,
                "agent": row.agent,
                "content": row.content,
            }
            for row in rows
        ]


def prompt_for(agent_type: str) -> str:
    with session() as db:
        row = db.get(AgentPromptTemplateRow, agent_type)
        return row.prompt if row else ""
