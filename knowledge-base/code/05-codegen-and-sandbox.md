# 代码生成与沙箱代码

文件：backend/src/services/codegen_service.py，backend/src/services/sandbox_service.py，frontend/src/pages/CodeGenDetail.tsx。
症状：方案通过后没有生成代码，代码页打不开，沙箱连通性测试成功但命令没有按内存或网络限制执行。

路由 /codegen/:taskId。封装 frontend/src/services/codegenService.ts。接口 backend/src/api/routes/codegen.py。方案审批通过后，backend/src/services/workflow_service.py 的 _after_solution_approved、_run_codegen 把需求改为 coding 并创建任务。代码审批通过后 _after_code_approved 才进入测试。沙箱函数 create_sandbox、execute_command、cleanup_sandbox。本地后端使用临时目录 opspilot_sandbox_*。项目里保存的内存、CPU、网络和非 root 设置只用于展示，本地执行器不会按这些数值强制限制。连通性测试只判断 backend 是否为 local。
