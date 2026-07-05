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
