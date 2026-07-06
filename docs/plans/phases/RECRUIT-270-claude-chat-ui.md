# RECRUIT-270 Claude-style Recruitment Chat UI

## 目标

把招聘助手从表单/卡片式操作页简化为 Claude 式对话体验，用户在对话里提交简历和岗位说明，并在任务对话中完成分析、复核和报告生成。

## 范围

- `agent-suite-web` 招聘新建页：移除结构化表单，改为单一对话输入入口。
- `agent-suite-web` 招聘任务详情页：把开始分析、取消运行、复核、生成报告组织成对话消息内的操作。
- 保留现有招聘后端 API、路由和数据结构。

## 不做

- 不接入真实 DeepSeek、ClamAV、Redis/MySQL/PDF 引擎。
- 不改数据库 schema、权限模型和后端任务工作流。
- 不删除任务列表和报告列表，它们仍作为历史记录入口。

## 验收标准

- `/recruitment/tasks/new` 不再展示结构化创建表单，只展示招聘助手对话入口。
- `/recruitment/tasks/:id` 不再以分散卡片展示运行和报告操作，核心操作出现在对话流内。
- 前端类型检查通过。
- 修改文件的格式检查通过。

## 验证记录

- 2026-07-06：`pnpm.cmd typecheck` 通过。
- 2026-07-06：`.\\node_modules\\.bin\\prettier.cmd --check src\\views\\recruitment\\RecruitNewTaskPage.vue src\\views\\recruitment\\RecruitTaskDetailPage.vue` 通过。
- 2026-07-06：Chrome 无头 smoke 通过；`/recruitment/tasks/new` 旧结构化表单数量为 0，对话线程为 1，composer 为 1；创建本地测试招聘任务后，任务详情页旧卡片数量为 0，对话消息为 3，操作入口包含“开始分析”。
