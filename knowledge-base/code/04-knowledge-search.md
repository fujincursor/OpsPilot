# 知识库检索代码

文件：backend/src/services/knowledge_service.py，backend/src/services/knowledge_indexer.py，frontend/src/pages/Knowledge.tsx。
症状：分析 Bug 或新需求时找不到相关代码，知识库未就绪，上传的文档无法被检索，技能说明打不开。

页面还有 frontend/src/pages/KnowledgeDetail.tsx，路由 /projects/:id/knowledge。技能正文弹窗 frontend/src/components/Skills/SkillContentModal.tsx。代码说明在 knowledge-base/code/。接口 backend/src/api/routes/knowledge.py 的 list_knowledge_bases、add_document、search_knowledge。分块约 1000 字，本地向量是 local-hash-256。对话检索在 deerflow_service._retrieve_project_knowledge，受技能 knowledge-retrieval 控制，会把文档正文交给模型。Bug 草稿只采用相关度高于 0.5 的结果，见 bugfix_agent.find_root_cause。生成方案时 solution_service 会把检索到的代码文档写进模型提示。技能文件读取 backend/src/services/skill_catalog.py，接口 GET /api/v1/skills/{skill_key}。
