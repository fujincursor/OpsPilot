# 测试执行代码

文件：backend/src/services/test_service.py，frontend/src/pages/TestDetail.tsx，backend/src/services/workflow_service.py。
症状：代码通过后测试没有开始，测试页没有结果，覆盖率不达标却进入完成，测试失败没有退回改代码。

路由 /tests/:testTaskId。接口 backend/src/api/routes/tests.py。测试重点说明会调用 agent_runtime.advise。代码审批通过后，workflow_service._after_code_approved 检查代码任务已完成且存在已通过的代码审核，然后把需求改为 testing，并按项目沙箱配置调用 test_service.create_test_task。质量门禁在 workflow_service._test_failed：失败数大于 0，或覆盖率低于 80%，会回到代码修改。测试默认不单独创建人工审核。技能：skills/opspilot/test-execution/SKILL.md。
