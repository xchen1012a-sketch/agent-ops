# agent-suite-web

企业多智能体应用平台的统一 Web 前端，提供法律咨询 / 智能招聘 / 智能问数三个模块入口。

## 技术栈

- Vue 3.5 + TypeScript 5.6
- Vite 5.4 + unplugin-auto-import + unplugin-vue-components（Element Plus 自动按需）
- Pinia 2 + pinia-plugin-persistedstate
- Vue Router 4
- Element Plus 2.8
- axios（统一拦截器 + 401 自动刷新 + 错误降级）
- 自研 SSE 客户端（fetch + ReadableStream，支持序列号去重、Last-Event-ID 重连、心跳）
- ECharts（智能问数图表）
- marked + DOMPurify（安全 Markdown 渲染，禁止 `<script>` / `<iframe>` / `javascript:` URI）
- Vitest 2 + @vue/test-utils（单元测试）
- Playwright 1.48（E2E）

详见 `docs/detailed-design.md`（WEB-410）。

## 目录结构

```text
src/
├── app/             # 应用壳：AppShell / AppHeader / AppSidebar / AppBreadcrumb / ErrorBoundary / GlobalToast
├── api/             # 业务 API 客户端（auth/legal/recruit/data 按模块拆分）
├── components/ui/   # 通用展示组件（PermissionGate / EmptyState / LoadingState / SafeMarkdown / SSEStatusIndicator ...）
├── features/        # 模块领域组件、composables、局部 store（按需新增）
├── lib/             # http-client / sse-client / markdown / config（环境变量注入）
├── router/          # Vue Router 配置 + 守卫
├── stores/          # Pinia stores（auth / toast / theme）
├── styles/          # tokens.css（设计 Token）+ global.css
├── types/           # 共享类型（api / auth / agent / sse）
└── views/           # 路由级页面
    ├── auth/        # 登录 / 登出 / 初始化
    ├── system/      # 404 / 403 / health
    ├── profile/     # 个人信息 / 偏好
    ├── legal/       # 法律咨询页面（admin/ 子目录）
    ├── recruitment/ # 智能招聘页面
    └── data/        # 智能问数页面
```

## 开发

```bash
pnpm install
pnpm dev         # 启动 Vite dev server，默认 http://localhost:5666
pnpm typecheck   # vue-tsc 类型检查
pnpm test        # Vitest 单元测试
pnpm build       # 构建到 dist/
pnpm preview     # 本地预览构建产物
pnpm e2e         # 运行 Playwright E2E
```

## 环境变量

参见 `.env.example`：

- `VITE_API_BASE_URL`：网关基地址（`suite-ops-nginx`）。
- `VITE_API_AUTH_PREFIX` / `VITE_API_LEGAL_PREFIX` / `VITE_API_RECRUITMENT_PREFIX` / `VITE_API_DATA_PREFIX`：模块前缀，需与 nginx 路由一致。
- `VITE_SESS_TIMEOUT_MINUTES`：前端会话空闲超时（分钟）。
- `VITE_DEFAULT_THEME`：默认主题（`light` / `dark` / `system`）。

Dev server 通过 `vite.config.ts` 中的 `server.proxy` 将 `/api/<auth|legal|recruitment|data>/*` 转发到本地后端服务；可用 `VITE_PROXY_*_TARGET` 覆盖目标地址。

## 模块边界

- 仅依赖公开 OpenAPI / SSE 契约；不直接访问 MySQL、DeepSeek、飞书。
- 三模块状态 store 不互相引用业务对象，仅共享 `useAuthStore`。
- 所有外部请求经 `src/lib/http-client.ts`，统一注入 JWT、X-Request-ID 与错误降级。
- Markdown 输出强制经 `DOMPurify` 净化，禁止 `v-html` 直接渲染未受控内容。

## 验证状态（FOUND-010 Step 1：前端壳）

- [x] 工具链接入：TypeScript / Prettier（嵌入 package.json）/ Vitest / Playwright / vue-tsc
- [x] WEB-410 §1 路由图全部占位
- [x] WEB-410 §4 Pinia stores（auth / toast / theme）
- [x] WEB-410 §7 SSE 客户端（fetch + ReadableStream + 心跳 + 重连）
- [x] WEB-410 §8 视觉 Token
- [x] WEB-410 §11 安全 Markdown（marked + DOMPurify）
- [x] Dockerfile 多阶段 + 非 root + HEALTHCHECK
- [x] `pnpm install` 通过（388 packages，无 supply-chain policy 失败）
- [x] `pnpm typecheck`（vue-tsc --noEmit）通过
- [x] `pnpm test` 19/19 通过（theme / toast / markdown / api-error-mapping）
- [x] `pnpm build` 通过（dist/ 完整产出，vue 115kb gzip 44kb，element-plus 898kb 待按需优化）
- [x] ESLint 9 flat config（`eslint.config.mjs`）+ `pnpm lint` 0 errors 0 warnings
- [x] `pnpm format:check` 全绿
- [x] `pnpm audit`（npm registry）：6 个漏洞（4 moderate / 1 high / 1 critical），分级处理见下方
- [ ] Playwright E2E 用例（待后端契约就绪后补）
- [ ] 视觉回归与 Lighthouse 性能预算（LCP < 2.5s，JS bundle gzip < 150kb 首屏）

### 已知前端依赖漏洞（pnpm audit，2026-07-05）

| 包 | 当前 | 修复 | 严重性 | 处理 |
|---|---|---|---|---|
| vitest | ^2.1.2 | >= 3.2.6 | critical | WEB-400 阶段升 major（v2→v3） |
| vite | ^5.4.8 | >= 6.4.3 | high | WEB-400 阶段升 major（v5→v6），同时带动 esbuild 升级 |
| vite | ^5.4.8 | >= 6.4.2 / 6.4.3 | moderate ×2 | 同上 |
| esbuild | 经 vite 间接引入 | >= 0.24.3 | moderate | 随 vite 升级（dev only） |
| echarts | ^5.5.1 | >= 6.1.0 | moderate (XSS) | WEB-400 阶段升 major（v5→v6） |

**为何不在 FOUND-010 修复**：vite/vitest/echarts 都是 major 升级，存在 breaking changes，需配合测试与视觉回归一起完成；FOUND-010 范围限定为「工程基线」，业务实现（WEB-400）阶段统一升级并完成回归。详见 `docs/plans/phases/FOUND-010-enterprise-foundation.md` 验证证据章节。
