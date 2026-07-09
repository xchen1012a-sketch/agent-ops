# FIX-web-login-api

## 现象 / 问题

用户反馈：前端登录页点击登录后没有看到登录接口请求返回；表现为登录接口未正确对接或点击未触发请求。

## 复现方式

1. 启动前端 `http://127.0.0.1:5666`。
2. 打开 `/login`。
3. 输入邮箱和密码后点击登录。
4. 观察 Network 是否出现 `/api/auth/login`。

## 初始证据

- `agent-suite-web/src/views/auth/LoginPage.vue` 存在模板文本/属性损坏：
  - `<h1>` 文本后出现 `?/h1>`，不是合法闭合标签。
  - 密码框 `placeholder="鑷冲皯 8 浣?` 缺少结束引号，后续 `show-password`、`size`、`@keyup.enter` 等属性可能被吞进 placeholder。
- `authClient.login()` 已封装为 `POST /login`，`authApi.baseURL` 为 `${VITE_API_BASE_URL}${VITE_API_AUTH_PREFIX}`，本地为 `http://127.0.0.1:5666/api/auth`。
- `Vite proxy` 已配置 `/api/auth` 到 `VITE_PROXY_AUTH_TARGET`，但当前 8081 认证服务未启动；正常修复后应至少能看到 `/api/auth/login` 请求并返回连接失败/代理错误，而不是无请求。

## 影响范围

- 前端登录页：`agent-suite-web/src/views/auth/LoginPage.vue`
- 登录 store/client 只做验证，不先改协议。
- 不影响法律/招聘/问数 Agent 后端。

## 不做事项

- 不新增真实认证服务。
- 不写入真实账号密码或生产密钥。
- 不修改招聘/问数并行模块。
- 不改变统一认证 API 契约。

## 分阶段修复步骤

### 阶段 1：修复登录页模板和提交触发

- 修复乱码导致的非法模板结构。
- 登录按钮改为表单 submit 语义，保证点击和回车都触发表单提交。
- 保留 `auth.login()` 调用路径。

验证：
- `pnpm.cmd typecheck`
- `pnpm.cmd test` 或相邻登录测试
- 浏览器/HTTP smoke：点击后应能发出 `/api/auth/login` 请求。

### 阶段 2：联调认证服务状态

- 确认 `/api/auth/login` 是否代理到 8081。
- 如果 8081 未启动，输出明确提示：接口已触发，但认证服务不可用。

验证：
- 直接请求 `http://127.0.0.1:5666/api/auth/login` 应有代理层响应或连接失败信息。

## 停止条件

- 需要新增/启动真实认证服务或数据库种子账号时，先等用户确认。
- 需要改统一认证契约时，先读 backend/API 规则并单独计划。

## 回滚 / 降级方式

- 回滚 `LoginPage.vue` 本次修改即可恢复原状态。
- 如果认证服务未就绪，保留登录页但提示本地认证服务未启动。

## 当前状态

- 2026-07-05：计划创建，准备执行阶段 1。

## 阶段执行记录

### 阶段 1 结果

状态：已完成。

修复点：
- 重写 `agent-suite-web/src/views/auth/LoginPage.vue` 中损坏的中文文案和非法模板结构。
- 修复密码输入框 `placeholder` 未闭合导致后续属性/事件可能被吞的问题。
- 登录按钮改为 `native-type="submit"`，由 `<el-form @submit.prevent="handleSubmit">` 统一触发提交。
- 新增 `agent-suite-web/tests/unit/login-page.spec.ts`，覆盖表单提交会调用 `auth.login()`。

验证证据：
- `pnpm.cmd typecheck`：通过。
- `pnpm.cmd test -- tests\\unit\\login-page.spec.ts`：通过，7 files / 34 tests passed（该 pnpm 参数会跑全量 vitest）。
- `pnpm.cmd lint`：通过。
- `pnpm.cmd format:check`：通过。
- `pnpm.cmd test`：通过，7 files / 34 tests passed。
- `pnpm.cmd build`：通过；保留既有 warning：Element Plus chunk > 500k、echarts empty chunk、@vueuse/core PURE 注释 warning。

### 阶段 2 结果

状态：已完成。

验证证据：
- `POST http://127.0.0.1:5666/api/auth/login` 已进入前端 Vite 代理层。
- Vite 日志显示：`http proxy error: /api/auth/login`，根因是 `connect ECONNREFUSED 127.0.0.1:8081`。

结论：
- 登录页现在会发出 `/api/auth/login` 请求。
- 当前仍不能登录的原因不是前端点击未触发，而是统一认证服务 `8081` 未启动/未实现。

### 阶段 3：本地开发认证 mock

状态：准备执行。

原因：当前统一认证服务 8081 未启动/未实现，前端登录接口会代理失败；为保证本地 Web 可演示和联调法律模块，新增仅 Vite dev server 生效的 /api/auth mock，不连接真实数据库、不写入真实密钥。

验证：登录按钮点击应触发 /api/auth/login，使用本地测试账号返回 token 和 profile，随后可进入 /legal。


### 阶段 3 结果

状态：已完成。

实现点：
- 新增 `agent-suite-web/dev-auth-plugin.ts`，仅在 Vite dev server 下提供本地 `/api/auth` mock。
- 修改 `agent-suite-web/vite.config.ts`：当 `VITE_ENABLE_DEV_AUTH=true` 时启用 mock，并跳过 `/api/auth` 到 8081 的代理。
- 修改 `agent-suite-web/.env.example`：记录 `VITE_ENABLE_DEV_AUTH=false` 默认值，避免共享/生产环境误启用。
- 修改本地忽略文件 `agent-suite-web/.env`：加入 `VITE_ENABLE_DEV_AUTH=true`。

本地账号：
- 管理员：`admin@example.com`
- 普通用户：`user@example.com`
- 密码规则：任意 8 位及以上本地测试口令；不在代码或文档中固化真实密码。

验证证据：
- `POST http://127.0.0.1:5666/api/auth/login` 使用管理员账号和 8 位以上测试口令返回 `dev-auth-token.dev-admin`。
- `GET http://127.0.0.1:5666/api/auth/me` 返回管理员 profile，role=`admin`。
- 错误密码返回 401。
- `GET http://127.0.0.1:5666/api/legal/v1/health/live` 返回 `{"status":"ok"}`，法律 Agent 代理仍正常。
- `GET http://127.0.0.1:5666` 返回 200。
- `pnpm.cmd typecheck`：通过。
- `pnpm.cmd lint`：通过。
- `pnpm.cmd format:check`：通过。
- `pnpm.cmd test`：通过，7 files / 34 tests passed。
- `pnpm.cmd build`：通过；保留既有 warning：Element Plus chunk > 500k、echarts empty chunk、@vueuse/core PURE 注释 warning。

安全边界：
- dev auth 只受本地 `.env` 开关控制，`.env` 已被 `.gitignore` 忽略。
- mock token 只用于本地开发，不作为生产认证实现。
