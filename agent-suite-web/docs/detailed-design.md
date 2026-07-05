# WEB-410 前端详细设计

> 状态：DESIGN-002 子阶段设计产出，待 FOUND-010 / WEB-420+ 编码实现。
> 真源：本文件 + `specification.md` + `adr/0007-unified-auth.md`、`adr/0009-recruitment-fairness.md`、`adr/0010-data-query-sql-safety.md`。

## 1. 路由图

```text
/login                          公开
/logout                         需登录
/                               需登录 -> /legal
/legal                          需登录 -> 重定向到 /legal/sessions
  /legal/sessions               会话列表
  /legal/sessions/:id           单会话流式问答
  /legal/history                历史搜索
  /legal/reports                报告列表
  /legal/reports/:id            报告详情
  /legal/admin/users            管理员：用户
  /legal/admin/categories       管理员：法律分类
  /legal/admin/knowledge        管理员：知识材料
  /legal/admin/prompts          管理员：Prompt 版本
/recruitment                    需登录 -> 重定向到 /recruitment/tasks
  /recruitment/tasks            任务列表
  /recruitment/tasks/new        新建分析
  /recruitment/tasks/:id        任务详情 + 复核
  /recruitment/materials        材料列表
  /recruitment/reports          报告列表
  /recruitment/admin/scoring    管理员：评分规则真源
  /recruitment/admin/audit      管理员：审计（含敏感属性对抗测试）
/data                           需登录 -> 重定向到 /data/sessions
  /data/sessions                会话列表
  /data/sessions/:id            对话查询 + 图表
  /data/history                 查询历史
  /data/admin/sql-audit         管理员：SQL 审计（完整 SQL 可见）
/me                             个人信息 + 密码修改
/settings                       偏好设置（主题、语言）
```

路由守卫：
- 未登录访问受保护路由 → 重定向 `/login?redirect=<path>`。
- 普通用户访问 `/admin/*` → 重定向 `/403`。
- 飞书 open_id 首次登录 → 强制走 `/onboarding` 设置密码（可选）。

## 2. 页面清单

| 路由 | 容器组件 | 权限 | 关键交互 |
|---|---|---|---|
| `/login` | `LoginPage` | 公开 | 表单 + 限流提示 |
| `/legal/sessions/:id` | `LegalSessionPage` | user+ | 流式问答 + 引用块 + 高风险提示 |
| `/legal/history` | `LegalHistoryPage` | user+ | 关键词搜索 + 时间筛选 |
| `/legal/reports/:id` | `LegalReportView` | user+ | Markdown 渲染 + PDF 下载 |
| `/legal/admin/knowledge` | `LegalKnowledgeAdmin` | admin | 上传材料 + 版本管理 |
| `/recruitment/tasks/new` | `RecruitNewTaskPage` | user+ | 上传简历 + JD + 触发分析 |
| `/recruitment/tasks/:id` | `RecruitTaskDetailPage` | user+ | 三档匹配 + 证据 + 复核按钮（admin 可见完整评分） |
| `/recruitment/admin/scoring` | `RecruitScoringAdmin` | admin | 评分规则真源查看（只读） |
| `/data/sessions/:id` | `DataSessionPage` | user+ | 对话 + 表格 + ECharts + 推荐追问 |
| `/data/admin/sql-audit` | `DataSqlAuditPage` | admin | SQL 列表 + 完整 SQL 详情 |
| `/me` | `ProfilePage` | user+ | 密码修改 |

## 3. 组件边界

**容器组件**（Container）：负责数据加载、状态、副作用。
**展示组件**（Presentational）：纯 UI，接收 props 与 emit events。

| 容器 | 负责的展示组件 |
|---|---|
| `LegalSessionPage` | `MessageList`、`MessageInput`、`StreamingBubble`、`CitationBlock`、`HighRiskAlert` |
| `RecruitTaskDetailPage` | `MatchResultCard`、`EvidenceList`、`GapAnalysis`、`InterviewQuestionList`、`AdminReviewPanel` |
| `DataSessionPage` | `DataChatWindow`、`QueryResultTable`、`EChartRenderer`、`FollowupSuggestions` |
| `AppShell` | `AppHeader`、`AppSidebar`、`AppBreadcrumb`、`ErrorBoundary`、`GlobalToast` |

通用展示组件（`src/components/ui/`）：`AsyncButton`、`EmptyState`、`LoadingState`、`PermissionGate`、`SafeMarkdown`、`FileDropzone`、`SSEStatusIndicator`。

## 4. 状态模型（Pinia stores）

| Store | 职责 | 持久化 |
|---|---|---|
| `useAuthStore` | 当前用户、JWT、角色、登录/登出/刷新 | refresh token cookie |
| `useLegalStore` | 法律会话列表、当前会话、消息流、SSE 状态 | 否 |
| `useLegalHistoryStore` | 历史搜索条件、结果、分页 | 否 |
| `useRecruitStore` | 招聘任务列表、当前任务、材料上传状态 | 否 |
| `useDataStore` | 智能问数会话、当前查询、SQL 审计（admin） | 否 |
| `useToastStore` | 全局通知队列 | 否 |
| `useThemeStore` | 主题、暗色模式 | localStorage |

跨模块不互相引用业务对象。`useAuthStore` 是唯一共享 store。

## 5. API 映射

| 页面 | 方法 | 路径 | 备注 |
|---|---|---|---|
| `LoginPage` | POST | `/api/auth/login` | 返回 access + 设置 refresh cookie |
| `LoginPage` | POST | `/api/auth/refresh` | access 过期时调用 |
| `ProfilePage` | POST | `/api/auth/change-password` | 失效所有 refresh |
| `LegalSessionPage` | POST | `/api/legal/v1/threads` | 创建会话 |
| `LegalSessionPage` | POST | `/api/legal/v1/threads/{id}/runs` | 触发流式问答 |
| `LegalSessionPage` | GET | `/api/legal/v1/runs/{run_id}/stream` | SSE |
| `LegalHistoryPage` | GET | `/api/legal/v1/sessions?keyword=&from=&to=&page=&size=` | |
| `LegalReportView` | GET | `/api/legal/v1/reports/{id}` | |
| `LegalReportView` | GET | `/api/legal/v1/reports/{id}/export?format=pdf` | |
| `LegalKnowledgeAdmin` | POST | `/api/legal/v1/admin/knowledge` | multipart |
| `RecruitNewTaskPage` | POST | `/api/recruitment/v1/tasks` | multipart 简历 + JD |
| `RecruitTaskDetailPage` | GET | `/api/recruitment/v1/tasks/{id}` | 三档匹配 |
| `RecruitTaskDetailPage` | POST | `/api/recruitment/v1/admin/tasks/{id}/review` | admin 签字 |
| `DataSessionPage` | POST | `/api/data/v1/threads` | |
| `DataSessionPage` | POST | `/api/data/v1/threads/{id}/runs` | |
| `DataSessionPage` | GET | `/api/data/v1/runs/{run_id}/stream` | SSE |
| `DataSqlAuditPage` | GET | `/api/data/v1/admin/sql-audit?page=&size=&user_id=` | admin |

`/api/auth/*` 由前端代理；其他 `/api/<legal|recruitment|data>/*` 由 Nginx 反向代理到各 Agent。

## 6. 错误矩阵

| 场景 | HTTP | 错误码 | UI 反馈 |
|---|---|---|---|
| 未登录 | 401 | `AUTH_REQUIRED` | 重定向 `/login` |
| Token 过期 | 401 | `AUTH_EXPIRED` | 静默 refresh，重试原请求 |
| 权限不足 | 403 | `AUTH_FORBIDDEN` | 重定向 `/403`，展示返回按钮 |
| 限流 | 429 | `RATE_LIMITED` | Toast：N 秒后重试，禁用按钮 |
| 服务不可用 | 503 | `AGENT_DEPENDENCY_TIMEOUT` | 降级页："AI 服务繁忙" |
| DeepSeek 超时 | 504 | `LLM_TIMEOUT` | "回答超时，请重试" 按钮 |
| 招聘文件超限 | 413 | `FILE_TOO_LARGE` | 表单内联提示 |
| 招聘文件类型不支持 | 422 | `FILE_TYPE_UNSUPPORTED` | |
| 招聘文件杀毒失败 | 422 | `FILE_SCAN_FAILED` | 提示用户检查文件 |
| 招聘解析失败 | 422 | `PARSE_FAILED` | 显示错误详情 + 重试 |
| 智能问数 SQL 拦截 | 422 | `SQL_POLICY_VIOLATION` | 友好提示"无法回答该问题"（普通用户不见 SQL） |
| 智能问数 MCP 不可用 | 503 | `MCP_UNAVAILABLE` | "查询服务暂不可用" |
| 法律高风险 | 200 + flag | n/a | 显示风险提示卡 + 线下渠道 |
| SSE 断开 | — | n/a | 自动重连 3 次（指数退避）；失败后保留已收消息，按钮重试 |
| 网络错误 | — | n/a | 全局 Toast + 自动重试 1 次 |

## 7. SSE 客户端策略

实现位置：`src/lib/sse-client.ts`。

- 基于 `EventSource` 或 `fetch + ReadableStream`（POST 用 fetch）。
- 事件去重：按 `event_id` 与 `sequence`，已收到的 `sequence` 丢弃旧序号。
- 断线恢复：保存最后 `sequence`，重连时通过 `Last-Event-ID` 头恢复。
- 停止：用户点击"停止"按钮，调用 `POST /runs/{run_id}/cancel` + 关闭流。
- 心跳：客户端 30 秒未收到任何事件（包括 heartbeat）→ 视为断线。
- 取消并发：切换会话时 abort 之前的 SSE 连接，避免消息错位。

## 8. 视觉 Token（CSS 自定义属性）

```css
:root {
  --color-bg: oklch(99% 0 0);
  --color-surface: oklch(98% 0 0);
  --color-text: oklch(18% 0 0);
  --color-text-muted: oklch(50% 0 0);
  --color-primary: oklch(58% 0.20 250);
  --color-accent: oklch(65% 0.18 280);
  --color-success: oklch(60% 0.15 145);
  --color-warning: oklch(70% 0.15 75);
  --color-danger: oklch(58% 0.22 25);
  --color-legal: oklch(58% 0.18 220);
  --color-recruit: oklch(60% 0.16 165);
  --color-data: oklch(62% 0.18 295);

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.05), 0 4px 12px rgba(0, 0, 0, 0.04);

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
}

@media (prefers-color-scheme: dark) {
  :root { /* 对应暗色变量 */ }
}
```

主题首期浅色为主，暗色模式标记为 beta。

## 9. 响应式断点

| 断点 | 宽度 | 布局 |
|---|---|---|
| `xs` | ≥ 375 | 单列、折叠菜单（汉堡）、底部 Tab 切换模块 |
| `sm` | ≥ 768 | 单列、侧边抽屉菜单 |
| `md` | ≥ 1024 | 双列：左导航 + 内容 |
| `lg` | ≥ 1440 | 双列 + 内容最大宽度 1200px 居中 |

不允许横向溢出。表格在 `xs/sm` 提供"卡片视图"切换。

## 10. 文件上传限制

- 招聘简历：`accept=".pdf,.txt"`，单文件 ≤ 10MB，PDF 页数 ≤ 20。
- 法律知识材料（admin）：`accept=".pdf,.txt,.md,.json"`，单文件 ≤ 50MB。
- 上传前校验 MIME 类型 + 文件签名（不只信扩展名）。
- 上传进度条 + 取消按钮 + 失败重试。

## 11. Markdown 安全渲染

法律 / 招聘 / 智能问数的回答可能含 Markdown。

- 使用 `marked` 或 `markdown-it` 解析。
- **必须**经 `DOMPurify` 净化后再 `v-html`。
- 配置白名单：禁用 `<script>`、`<iframe>`、`on*` 属性、`javascript:` URL。
- 允许的标签：`p`、`h1-h6`、`ul`、`ol`、`li`、`strong`、`em`、`blockquote`、`code`、`pre`、`a`（仅 https）、`table` 系列。
- 引用块 `<blockquote>` 应用 `CitationBlock` 样式，区别于普通引用。

## 12. 验收

- ESLint / Prettier / vue-tsc / Vitest 单元测试 / Playwright E2E 全部通过。
- 4 个断点（375/768/1024/1440）视觉回归通过。
- 关键 E2E：登录、法律流式问答、招聘复核、智能问数表格+图表、SQL 审计（admin）。
- 暗色模式（beta）关键页面可读。
- Lighthouse 性能预算：LCP < 2.5s，JS bundle gzip < 150kb（首屏）。
