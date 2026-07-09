# MVP-002 Chat Composer Interaction

## 目标

把 MVP 保留下来的聊天入口收敛成更接近 ChatGPT 的低成本交互：固定输入区、Enter 直接发送、Shift + Enter 换行、支持粘贴文本类文件并对图片粘贴给出软提示。

## 范围

- 新增统一聊天输入组件，复用到法律咨询、智能问数的入口页/详情页，以及招聘新建任务页。
- 输入框支持 Enter 发送，Shift + Enter 换行，发送中禁用重复提交。
- 粘贴文件时：
  - 图片文件不进入 OCR 或上传流程，显示友好提示。
  - 文本类文件读取内容并追加到输入框。
  - 其他非图片文件只显示附件提示，明确当前发送仍以输入框文本为准。
- 保持现有 API、SSE、路由和后端不变。

## 不做

- 不接 OCR。
- 不实现真实文件上传、文件解析、PDF/Word 解析或后端附件存储。
- 不改招聘任务 API 和后端任务模型；招聘页只在前端把单输入内容拆成现有 `resume_text` / `jd_text`。
- 不重构页面布局、路由或全局设计系统。

## 验收标准

- 法律咨询、智能问数入口页和详情页都使用统一 Chat Composer；招聘新建任务页提供单输入快速创建入口。
- Enter 发送、Shift + Enter 换行行为可测试。
- 粘贴图片不会提交或插入输入框，并显示软提示。
- 粘贴文本文件会追加文件内容到输入框。
- 前端 typecheck 和相关组件测试通过，或记录失败原因。

## 验证记录

- 2026-07-05：
  - `agent-suite-web`: `npm.cmd test -- chat-composer agent-chat-landing` 通过，2 files / 6 tests passed。
  - `agent-suite-web`: `npm.cmd run typecheck` 通过。
  - `agent-suite-web`: `npm.cmd run build` 通过；Vite 输出既有 chunk size / Rollup annotation warning。
  - 浏览器 smoke：`/legal/sessions` 已渲染统一 `ChatComposer`，输入框、Enter 提示和文件按钮可见。
  - 浏览器 smoke：`/recruitment/tasks/new` 已渲染统一 `ChatComposer`，快速创建提示、文件按钮和结构化详情可见。
  - 启动阶段刷新项目事实脚本时，PowerShell 执行策略拦截 `.ai-spec\scripts\refresh-project-facts.ps1`；本阶段未绕过全局策略。

## 回滚方式

- 恢复 `AgentChatLanding.vue`、法律详情页、问数详情页到各自原有 composer。
- 删除新增 Chat Composer 组件和对应测试。
