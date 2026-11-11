# 对话与需求代码

文件：frontend/src/pages/Chat.tsx，frontend/src/pages/RequirementDetail.tsx，backend/src/services/deerflow_service.py。
症状：对话里分出了 Bug 但需求列表没有工单，咨询也被推进到编码，知识库未就绪时无法提交需求。

页面还有 frontend/src/components/Chat/ChatWindow.tsx、frontend/src/pages/Requirements.tsx。路由 /chat、/requirements/:reqId。后端 backend/src/api/routes/chat.py 的 list_chats、get_chat。分类和知识引用在 deerflow_service.chat、_retrieve_project_knowledge。是否允许建单由 backend/src/services/workflow_service.py 的 knowledge_block、open_solution_review 决定。咨询类型 question 不生成方案。需求状态写入 backend/src/services/requirement_service.py 的 update_status、set_failure_reason。失败原因在 Requirement.failure_reason，页面用 FlowStateBanner 展示。
