# 任务路由

## 基本流程

1. 先判断任务等级。
2. 再选择 0-2 个最相关 skills。
3. 读取最小必要上下文。
4. 执行任务。
5. 用证据完成验证。

## 分级

- L0：问答、解释、状态查询，不改文件。
- L1：单文件或小范围修改，不影响 API、数据库、权限、进程、部署。
- L2：一个模块内修改，需要测试验证。
- L3：涉及 API/DTO、数据库、权限、安全、进程、外部服务、前后端联调。
- L4：项目初始化、架构调整、阶段切换、跨仓协作、规则接入。

## Skill 选择

- 默认 project-first：先用项目 .ai-spec/skills/。
- 项目 skill 不足时，可读取用户本地 skill 补充，但必须先说明缺口。
- 用户可指定 project-only 或 local-first。
- 本地 skill 不能覆盖项目红线、契约、任务等级和验证要求。
- 任何模式都不允许自动修改用户全局 Claude / Codex 配置。

## 全局规则边界

Claude Code、Codex 或其它工具可能会把用户全局 rules、memory、skills 或 system prompt 预先注入上下文。项目规则无法阻止这些内容出现，但可以规定冲突处理：

- 系统/开发者指令优先级最高。
- 在系统/开发者指令之后，当前项目 `.ai-spec/` 是项目事实、任务路由、验证要求和交付格式的优先来源。
- 全局 rules 只能补充通用能力，不得覆盖当前项目的 `project-facts.md`、docs/plans、contracts、redlines、task-routing 和 skills。
- L2 及以上任务最终输出必须说明读取了哪些项目规则和项目 skills。
- 如果任务命中了项目 skill，但实际读取项目 skill 数量为 0，必须停止继续实现，回到 `.ai-rules/task-routing.md` 重新路由。
- 用户明确指定 `project-only` 时，不读取用户本地 skills；已注入的全局内容只能作为背景，不作为执行依据。

## 模块化边界

- 写代码和报告必须保持模块化：职责单一、边界清楚、证据可查。
- 写代码必须保持最小必要改动：能用现有结构小改解决，就不新建大框架、不做未要求的扩展、不顺手重构无关代码。
- 如果任务会破坏现有模块边界，必须先报告并等待用户确认。
- 涉及新增模块、多文件实现、重构或复杂交付时，读取 `.ai-rules/modularity-output.md`。

## 修复和 Review

修 bug、找 bug、测试失败恢复、运行异常排查、代码 review 后继续修复时：

- L0 解释错误、只读 review、单点问答：可以不写计划文件。
- L1 明确小改：可在回复里给简短步骤，不强制落文件。
- L2 及以上 bugfix / debugging / review-fix：必须先写入或更新 `docs/plans/phases/<FIX-or-REV>-<short-name>.md`。
- 如果项目已有 `docs/plans/current.md`，必须把当前阶段指向该修复计划；如果没有，只创建本次修复计划文件。
- 计划文件必须包含：现象/问题、证据、影响范围、不做事项、分阶段修复步骤、每阶段验证方式、停止条件、回滚/降级方式。
- 写完计划后只执行第一阶段；每阶段完成后更新状态和验证证据。
- 发现计划外文件、跨模块根因或需要扩大范围时，先更新计划并报告，等用户确认后再继续。

## Skill 路由

### 领域 skill

- 项目初始化、阶段切换、架构变化：`project-planning`
- 项目业务域、模块词表、项目专属约定：`project-domain`
- Web 前端、UI、API client：`frontend-web`
- REST/OpenAPI、DTO、service/repository：`backend-api`
- 数据库设计、迁移、索引：`database`
- Agent、Skill、工作流节点：`ai-workflow`
- ComfyUI、TTS、FFmpeg、素材、导出：`media-pipeline`
- 测试、验证、回归：`testing-verification`
- 本地启动、端口、健康检查：`deployment-local`

### 横向质量 skill

- 多文件变更、功能开发、重构、阶段任务：`incremental-implementation`
- 测试失败、构建失败、运行异常、进程闪退：`debugging-recovery`
- 用户要求 review、合并前检查、AI 代码把关：`code-review-quality`
- 认证、权限、输入、文件、路径、密钥、外部服务：`security-hardening`
- ADR、API 文档、验收证据、日志、指标、追踪：`documentation-observability`

## 组合建议

- L0：通常不读 skill。
- L1：最多 1 个领域 skill。
- L2：1 个领域 skill，可加 `testing-verification` 或 `incremental-implementation`。
- L3：1 个领域 skill + 1 个横向质量 skill。
- L4：`project-planning` + 一个最关键的领域或横向质量 skill。

## 不要过度升级

- 不因不确定就直接提升到 L4。
- 不把问答任务当成开发任务。
- 不把小改动升级成项目重构。
- 不为了使用 skill 而读取无关 skill。
- 不一次读取超过 2 个 skill，除非用户明确要求全面审计。

