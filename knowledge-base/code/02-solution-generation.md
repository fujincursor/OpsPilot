# 方案生成代码

文件：backend/src/services/solution_service.py，backend/src/services/agents/bugfix_agent.py，frontend/src/pages/SolutionDetail.tsx。
症状：不同 Bug 生成相同修复方案，方案生成失败看不到原因，重新生成后仍有多份待审核方案，方案页 Markdown 显示成原文。

frontend/src/pages/RequirementDetail.tsx 的 handleGenerateSolution 调用 frontend/src/services/solutionService.ts。后端 backend/src/api/routes/solutions.py 的 generate_solution 在已有待审核方案时返回 409，regenerate_solution 会作废旧方案。核心函数还有 has_pending_solution、collapse_pending_solutions。Bug 草稿来自 bugfix_agent.generate_fix_solution，未命中关键词时类型是 unknown，所以不同 Bug 会得到同一套通用步骤。模型重写走 backend/src/services/agent_runtime.py 的 advise，以及 deerflow_service.complete_text，不调用网页抓取。新需求方案来自 backend/src/services/agents/feature_agent.py。技能：skills/opspilot/bugfix-solution/SKILL.md、skills/opspilot/feature-design/SKILL.md。
