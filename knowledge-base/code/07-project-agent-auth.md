# 项目、Agent 与登录代码

文件：frontend/src/pages/ProjectSettings.tsx，backend/src/services/agent_runtime.py，frontend/src/pages/Login.tsx。
症状：项目设置里的 Agent 或技能没有参加执行，禁用技能后仍然生成方案，登录后接口 401，刷新页面回到登录页。

页面还有 frontend/src/pages/ProjectDetail.tsx、frontend/src/pages/ProjectProfile.tsx。令牌保存在 frontend/src/services/authService.ts 的 auth_token、refresh_token。后端 backend/src/api/routes/auth.py 的 login、refresh_token、get_current_user_info。默认账号 admin / admin123。Agent 是否启用、主技能是否启用，由 agent_runtime.require、_require_skill、render_task 决定。主技能：Lead 用 requirement-analysis，BugFix 用 bugfix-solution，Feature Design 用 feature-design，CodeGen 用 code-generation，Test 用 test-execution。模型名必须与 DeerFlow 配置一致，当前是 deepseek-v4。
