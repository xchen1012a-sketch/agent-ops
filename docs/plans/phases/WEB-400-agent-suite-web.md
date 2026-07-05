# WEB-400 统一 Web 前端并行开发计划

## 状态

- 状态：并行阶段已启动；第一切片为前端健康与配置检查面板。
- 模块：`agent-suite-web`
- 执行边界：不修改招聘 Agent、智能问数 Agent、法律 Agent 后端代码；不修改其它 AI 的并行改动。
- 计划依据：
  - `docs/plans/modules/agent-suite-web.md`
  - `agent-suite-web/docs/specification.md`
  - `agent-suite-web/docs/detailed-design.md`
  - `.ai-spec/.ai-rules/development-standards.md`

## 阶段目标

在不阻塞招聘与智能问数后端并行开发的前提下，推进统一 Web 前端基础搭建和可独立验证的壳层能力。优先完成公共配置、路由、健康检查、降级状态、基础 UI 状态与法律模块可复用前置能力；招聘和智能问数业务页在后端契约稳定前只做占位或 mock 边界。

## 范围

1. 前端 App Shell、路由、导航、响应式与主题基础。
2. API/SSE client 公共边界、错误映射、配置检查和服务降级状态。
3. 法律模块已稳定契约的前端接入前置工作。
4. 招聘与智能问数模块的占位、降级和契约等待状态，不猜测未冻结字段。
5. 前端质量门禁：typecheck、lint、format、unit test、build。

## 不做事项

- 不修改 `agents/recruitment-assistant-agent` 或 `agents/data-query-agent`。
- 不依赖后端私有字段，不读取数据库，不拼接 Prompt，不生成 SQL。
- 不接真实 DeepSeek、MySQL、飞书或生产服务。
- 不在浏览器保存密钥、Token 以外的敏感凭据或生产配置。
- 不把 mock 状态伪装成真实后端完成状态。
- 不提交或推送 Git，除非用户明确要求。

## 切片计划

### WEB-421：前端健康与配置检查面板

- 目标：把 `/health` 从单一法律 Agent 探测升级为统一前端健康面板。
- 改动范围：
  - `agent-suite-web/src/views/system/HealthPage.vue`
  - `agent-suite-web/src/lib/`
  - `agent-suite-web/src/types/`
  - `agent-suite-web/tests/unit/`
- 输出：
  - 三 Agent `/health/live` 检查状态。
  - API 前缀、会话超时等非敏感配置展示。
  - 服务不可用、降级、检查中状态 UI。
- 验收：
  - 单测覆盖状态映射与配置检查。
  - `pnpm typecheck`、`pnpm lint`、`pnpm test`、`pnpm build` 通过或记录未验证原因。

### WEB-430：公共交互基础设施补强

- 目标：补齐 HTTP/SSE client 在页面层的可复用状态投影。
- 验收：成功、超时、断线、重复事件、取消、401/403/429/5xx 的 mock 测试覆盖。

### WEB-440：法律咨询页面第一条主链路

- 目标：优先使用法律 Agent 当前公开 API 契约打通会话/问答/报告读取前端主路径。
- 验收：不依赖招聘/问数；loading/error/empty/success 状态覆盖；关键组件测试通过。

### WEB-450 / WEB-460：招聘与智能问数页面

- 目标：等待对应 Agent 契约稳定后再接入真实字段；此前只保留占位、降级和 mock 边界。

## 停止条件

- 需要猜测未进入 OpenAPI/规格的字段。
- 需要修改后端 API、DB、权限或跨 Agent 边界。
- 招聘/智能问数并行改动与前端契约冲突。
- 前端质量门禁失败且原因不明。

## 验证命令

在 `agent-suite-web` 下执行：

```powershell
pnpm typecheck
pnpm lint
pnpm format:check
pnpm test
pnpm build
```

## 执行证据

- 2026-07-05：完成 `WEB-421` 第一切片。新增统一 Web 前端健康与配置检查面板，`/health` 可展示法律咨询、智能招聘、智能问数三个 Agent 的公开 `/health/live` 探测状态，并展示 API 前缀与会话超时等非敏感运行配置；未修改任何后端 Agent，未连接真实生产服务。验证：
  - `pnpm.cmd typecheck`：通过。
  - `pnpm.cmd lint`：通过。
  - `pnpm.cmd format:check`：通过。
  - `pnpm.cmd test`：5 files / 25 tests passed。
  - `pnpm.cmd build`：通过；保留既有 Vite/Rollup warning：Element Plus chunk 大于 500 kB、`echarts`/`markdown` 空 chunk、`@vueuse/core` PURE 注释提示。
  - `git diff --check -- docs/plans/phases/WEB-400-agent-suite-web.md agent-suite-web/src/views/system/HealthPage.vue agent-suite-web/src/lib/service-health.ts agent-suite-web/src/types/health.ts agent-suite-web/tests/unit/service-health.spec.ts`：通过，仅提示 Windows CRLF 工作区转换警告。
- 2026-07-05：完成 `WEB-440` 法律模块前两片。新增法律 Agent 前端类型与 API client；`legalApi` 按法律 Agent 当前公开边界注入 `x-user-public-id`；实现法律会话创建页、会话详情问答页、历史咨询页和 Markdown 报告详情页。未实现 `GET /sessions` 会话列表，因为法律 Agent 当前公开代码尚未提供该接口；未接真实 DeepSeek/RAG/token streaming。验证：
  - `pnpm.cmd typecheck`：通过。
  - `pnpm.cmd lint`：通过（一次与 Vitest timestamp 临时文件相关的 ESLint ENOENT 竞态，重跑通过）。
  - `pnpm.cmd format:check`：通过。
  - `pnpm.cmd test`：6 files / 30 tests passed。
  - `pnpm.cmd build`：通过；保留既有 Vite/Rollup warning：Element Plus chunk 大于 500 kB、`echarts` 空 chunk、`@vueuse/core` PURE 注释提示。
  - `git diff --check -- agent-suite-web/src/types/legal.ts agent-suite-web/src/api/legal.ts agent-suite-web/src/lib/http-client.ts agent-suite-web/src/lib/config.ts agent-suite-web/src/views/legal/LegalSessionListPage.vue agent-suite-web/src/views/legal/LegalSessionPage.vue agent-suite-web/src/views/legal/LegalHistoryPage.vue agent-suite-web/src/views/legal/LegalReportView.vue agent-suite-web/tests/unit/legal-client.spec.ts`：通过，仅提示 Windows CRLF 工作区转换警告。
- 2026-07-05：完成 `WEB-440` 法律反馈与高风险审核切片。扩展法律前端类型与 API client，接入回答反馈、高风险审核入队、管理员审核列表与处理接口；会话详情页为助手回答提供反馈和加入审核操作；新增 `/legal/admin/reviews` 管理员高风险审核页面并加入侧边栏。未修改法律 Agent 后端，未接真实外部服务。验证：
  - `pnpm.cmd typecheck`：通过。
  - `pnpm.cmd lint`：通过。
  - `pnpm.cmd format:check`：通过。
  - `pnpm.cmd test`：6 files / 33 tests passed。
  - `pnpm.cmd build`：通过；保留既有 Vite/Rollup warning：Element Plus chunk 大于 500 kB、`echarts` 空 chunk、`@vueuse/core` PURE 注释提示。
  - `git diff --check -- agent-suite-web/src/types/legal.ts agent-suite-web/src/api/legal.ts agent-suite-web/src/views/legal/LegalSessionPage.vue agent-suite-web/src/views/legal/admin/HighRiskReviewAdminPage.vue agent-suite-web/src/router/index.ts agent-suite-web/src/app/AppSidebar.vue agent-suite-web/tests/unit/legal-client.spec.ts`：通过，仅提示 Windows CRLF 工作区转换警告。
- 2026-07-05：完成 `WEB-440` 法律报告列表与 admin 契约等待切片。`LegalReportListPage` 使用已公开 `GET /consultation-records` 作为报告入口；新增 `ContractPendingState`，并将法律分类、知识材料、Prompt 版本、用户管理四个 admin 页面替换为明确的契约等待/降级状态。经扫描法律 Agent 当前 endpoints，未发现分类、知识材料、Prompt、用户管理公开接口，因此未猜测字段或发起伪 API 调用。验证：
  - `pnpm.cmd typecheck`：通过。
  - `pnpm.cmd lint`：通过。
  - `pnpm.cmd format:check`：通过。
  - `pnpm.cmd test`：6 files / 33 tests passed。
  - `pnpm.cmd build`：通过；保留既有 Vite/Rollup warning：Element Plus chunk 大于 500 kB、`echarts` 空 chunk、`@vueuse/core` PURE 注释提示。
  - `git diff --check -- agent-suite-web/src/components/ui/ContractPendingState.vue agent-suite-web/src/views/legal/LegalReportListPage.vue agent-suite-web/src/views/legal/admin/CategoryAdminPage.vue agent-suite-web/src/views/legal/admin/KnowledgeAdminPage.vue agent-suite-web/src/views/legal/admin/PromptAdminPage.vue agent-suite-web/src/views/legal/admin/UserAdminPage.vue`：通过，仅提示 Windows CRLF 工作区转换警告。
