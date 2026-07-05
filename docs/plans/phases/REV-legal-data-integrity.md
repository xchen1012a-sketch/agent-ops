# REV 法律数据设计与审计完整性修复

## 状态

已完成第一阶段：设计真源已对齐，最小审计一致性校验及回归测试已通过。第二阶段返回 `LEGAL-100 / LEGAL-130` 后分批执行。

## 现象 / 问题

1. `LEGAL-100` 后续表清单包含 `consultation_records`、`reports` / `export_tasks`，但法律详细设计没有对应表结构。
2. `knowledge_materials`、`prompt_versions`、`high_risk_reviews`、`feedbacks` 的用户/消息关联和约束不完整。
3. `LegalDataService.create_agent_run` 接受原始 `thread_id`、`user_id`，创建前未确认会话确实属于该用户。
4. `FOUND-010` 的 Docker 健康检查证据保留旧路径；当前代码已在提交 `76556f5` 修正为 `/v1/health/live`。
5. 根项目事实刷新脚本只扫描根目录清单，且可能记录写入前的 Git 状态；但 `.ai-spec/` 被当前项目事实标记为只读，本轮不修改。

## 证据

- `docs/plans/current.md` 与 `docs/plans/phases/LEGAL-100-legal-consulting-agent.md` 列出后续表。
- `agents/legal-consulting-agent/docs/detailed-design.md` 的 ER 图包含 ConsultationRecord / Report，但数据库设计缺少对应 DDL。
- `agents/legal-consulting-agent/src/legal_consulting_agent/application/services/legal_data_service.py` 的 `create_agent_run` 直接持久化调用方提供的用户和会话标识。
- 当前法律数据 service/repository 尚未接入 API 或 workflow，调用方仅为单元测试。

## 影响范围

- `agents/legal-consulting-agent/docs/detailed-design.md`
- `agents/legal-consulting-agent/src/legal_consulting_agent/application/services/legal_data_service.py`
- `agents/legal-consulting-agent/tests/unit/test_legal_data_service.py`
- `docs/plans/current.md`
- `docs/plans/phases/LEGAL-100-legal-consulting-agent.md`
- 本计划文件

## 不做事项

- 不新增或修改数据库迁移。
- 不新增后续 ORM、repository、API、前端页面或工作流节点。
- 不修改公开 API、数据库权限、认证架构或其他 Agent。
- 不修改冻结的 `FOUND-010` 阶段文件。
- 不修改 `.ai-spec/`、不重写 Git 历史、不提交或推送。

## 分阶段修复步骤

### 第一阶段：设计真源与审计入口

1. 补齐咨询记录和报告/导出任务的逻辑表设计。
2. 补齐未来表的外键、评分范围、唯一性和路径语义。
3. 明确 AgentRun 采用保留审计快照、不建立用户/会话外键，但创建前必须校验用户拥有会话。
4. 为校验成功和越权/不存在场景补充单元测试。
5. 在本计划记录健康检查修正，不修改冻结历史文件。

验证：

- `uv run pytest tests/unit/test_legal_data_service.py`
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src`

### 第二阶段：后续表实现

不在本次 review-fix 中执行。返回 `LEGAL-100 / LEGAL-130` 后，按已确认设计分批生成 ORM、Alembic 迁移、repository、service 和测试。

## 停止条件

- 需要修改现有 API、已生成迁移、数据库权限或认证边界。
- 咨询记录与消息模型无法在现有规格内消解。
- 报告导出需要引入对象存储、队列或新的运行服务。
- 修复需要修改其他 Agent 或前端实现。

## 回滚 / 降级

- 文档变更可按本计划涉及的段落独立回退。
- service 校验与相邻测试可独立回退，不影响 ORM 和迁移。
- 如设计未通过验证，保持当前六表实现并停止进入后续表开发。

## 验证证据

2026-07-05 在 `agents/legal-consulting-agent` 执行：

- `uv run pytest tests/unit/test_legal_data_service.py -q`：6 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：56 files already formatted。
- `uv run mypy src`：42 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：31 passed，覆盖率 80%。
- 静态调用检索：`LegalDataService` / `SqlAlchemyLegalDataRepository` 尚未接入 API 或 workflow；本次行为变化仅影响现有单元测试入口和未来调用方。
- 数据库迁移：未修改，未执行迁移验证。

未处理项：

- `.ai-spec/scripts/refresh-project-facts.ps1` / `.sh` 的根目录扫描和 Git 状态记录问题确认存在，但 `.ai-spec/` 被当前项目事实标记为只读，本次未修改。
- 现有 Git 提交粒度和分支历史不重写；后续提交按模块和主题拆分。
- `FOUND-010` 为冻结历史阶段，不修改原证据；Docker 健康检查路径修正由提交 `76556f5` 保留。
