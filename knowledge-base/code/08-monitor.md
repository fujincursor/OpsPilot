# 监控页代码

文件：frontend/src/pages/Monitor.tsx，frontend/src/pages/MonitorTask.tsx，backend/src/api/routes/analytics.py。
症状：监控页面打不开，会话记录加载失败，监控数字和需求状态不一致，等待审批数量不对。

路由 /monitor 与 /monitor/:requirementId。工作台 frontend/src/pages/Dashboard.tsx、frontend/src/pages/Home.tsx 也会读取待审核数量和完成率。统计接口 /analytics/global，以及 /projects/{project_id}/analytics/dashboard、trends、agents、quality、funnel。阶段名称由 backend/src/services/workflow_service.py 的 stage_label 给出。待审核数量来自审核项状态 pending、in_review，不是方案列表里的全部历史记录。暂停、恢复和停止在 workflow_service.pause、resume、stop。
