# FIX-WEB-icons-display

## 现象

用户反馈：Web 页面大量图标无法显示。范围集中在 `agent-suite-web` 的壳层导航、顶部栏以及各页面 Element Plus icon 使用处。

## 复现方式

1. 启动前端：`pnpm dev -- --host 0.0.0.0 --port 5666` 或既有 5666 前端进程。
2. 登录后访问 `/legal`。
3. 观察左侧导航、顶部栏、按钮/状态图标。
4. 预期：图标正常渲染；实际：多个 `<el-icon>` 内为空或组件无法解析。

## 初始证据

- `vite.config.ts` 只配置了 `ElementPlusResolver()`，它解析 Element Plus 组件，不保证解析 `@element-plus/icons-vue` 图标组件。
- `components.d.ts` 中没有 `Menu`、`Document`、`ChatDotRound`、`Sunny`、`Moon` 等图标组件声明。
- 当前代码大量使用：
  - 静态图标：`<Menu />`、`<ArrowDown />`
  - 字符串动态图标：`<component :is="group.icon" />`
- Vue 字符串动态组件依赖全局注册；当前未见全局注册 Element Plus icons。

## 影响范围

- 仅前端图标渲染与可访问性。
- 不改变 API、认证、数据库、后端 Agent。

## 不做事项

- 不新增图标库依赖。
- 不修改三个 Agent 后端。
- 不重构路由、权限、API client。
- 不覆盖其它 AI 在招聘/问数模块的改动。

## 修复阶段

### 阶段 1：定位根因

- 搜索所有 Element Plus icon 使用方式。
- 确认是否存在全局注册或自动解析。
- 建立根因假设。

验证：静态检查 + `typecheck`。

### 阶段 2：最小修复

- 在 `main.ts` 全局注册项目已使用的 Element Plus icon 组件。
- 保留现有模板写法，避免大面积替换页面。
- 覆盖静态组件和字符串动态组件。

验证：`typecheck`、`lint`、`test`、`build`。

### 阶段 3：回归检查

- 确认 `components.d.ts`/运行时解析不再依赖未注册图标。
- 如可用，浏览器 smoke 检查页面图标。

验证：本地浏览器或构建产物。

## 停止条件

- 若 `@element-plus/icons-vue` 在本地不可解析，停止并改为用户确认是否增加直接依赖。
- 若修复需要大规模替换业务页面组件，先报告范围。

## 回滚方式

- 回滚 `main.ts` 中 icon 注册代码即可恢复原状。

## 阶段执行记录

### 阶段 1：定位根因 - 已完成

证据：

- `node -e "require('@element-plus/icons-vue')"` 在 `agent-suite-web` 下报 `MODULE_NOT_FOUND`。
- `components.d.ts` 未生成 `Menu` / `Document` / `ChatDotRound` / `Close` 等图标组件声明。
- 源码存在未注册图标写法：`<Menu />`、`<Close />`、`<DocumentChecked />`、`<component :is="group.icon" />`、`<component :is="props.icon" />`。

根因：项目只配置了 Element Plus 组件解析，没有稳定暴露/注册 `@element-plus/icons-vue` 图标组件；字符串动态组件也不会自动解析为图标。

### 阶段 2：最小修复 - 已完成

改动：

- 新增 `agent-suite-web/src/components/ui/AppIcon.vue`，提供项目当前实际使用的本地 SVG 图标。
- 替换：
  - `AppHeader.vue` 的 `Menu` / `Sunny` / `Moon` / `ArrowDown`
  - `AppSidebar.vue` 的模块/子项/展开折叠图标
  - `GlobalToast.vue` 的通知类型图标和关闭图标
  - `ContractPendingState.vue` 的 `DocumentChecked`
  - `EmptyState.vue` 的动态 icon
- 同步修复 `GlobalToast.vue`、`ContractPendingState.vue` 中与图标按钮相关的乱码 aria 文案。

### 阶段 3：验证 - 已完成/部分受阻

已通过：

- `pnpm.cmd format:check`
- `pnpm.cmd lint`
- `pnpm.cmd test`：10 files / 53 tests passed
- 图标源码扫描：未发现剩余 `<Menu />`、`<Close />`、`<DocumentChecked />`、`<component :is="*.icon" />` 等未注册图标写法。

受阻：

- `pnpm.cmd typecheck` / `pnpm.cmd build` 当前失败在并行智能问数页面：
  - `src/views/data/DataSessionListPage.vue(33,36)`：`unknown` 传入 `RequestErrorInput`
  - `src/views/data/DataSessionListPage.vue(117,39)`：`data` 可能为 `null`
- 该文件属于当前并行智能问数前端改动，不属于本次图标根因范围，未继续修改。

### 停止/回滚

- 本次没有新增依赖，也没有改后端/API/DB。
- 回滚方式：移除 `AppIcon.vue` 并恢复上述组件中的图标引用。
