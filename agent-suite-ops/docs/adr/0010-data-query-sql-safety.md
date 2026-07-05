# ADR-0010：智能问数 SQL 安全策略

- 状态：已确认
- 日期：2026-07-04
- 阶段：DESIGN-002

## 背景

智能问数 Agent 的核心风险是 LLM 生成 SQL 后直接执行可能造成越权读取、DoS、数据泄露或绕过权限。课件原有 MCP 工具节点 + 安全校验节点的链路必须保留并加固。

## 决策

### 查询链路

- 沿用课件 MCP server 作为查询主链路；MCP server 实现 tool schema、超时 30 秒、错误码映射。
- 数据库账号分离：
  - `shop_db` 使用独立只读 MySQL 账号，仅授予 `SELECT` 权限；禁止访问 `mysql`、`information_schema`、`performance_schema`、`sys`。
  - `data_query_agent_db` 使用读写账号，存会话、审计、Prompt 版本等运行态数据。
- LLM 生成 SQL 后必须依次通过：Pydantic Schema 校验 → sqlglot AST 解析 → 白名单校验 → 资源限制 → 才允许进入 MCP 执行。

### SQL 类型与形态

- 仅允许 `SELECT`。
- 允许形态：简单 SELECT、聚合 + GROUP BY + HAVING、CTE、子查询、JOIN（仅白名单内表）。
- 禁止：DDL、DML、`UNION`、注释 `--` `/* */`、分号、多语句、文件函数、延时函数、用户变量、`INTO`、存储过程、`LOAD_FILE`、系统 schema。

### 白名单

- 表白名单：`shop_db` 中所有维度表、事实表、宽表（具体清单在 `DATA-310` 形成 YAML 真源）。
- 列白名单：所有白名单表的列。
- 函数白名单：聚合函数（`SUM`/`COUNT`/`AVG`/`MIN`/`MAX`）、日期函数（`DATE`/`DATE_FORMAT`/`YEAR`/`MONTH`）、字符串函数（`SUBSTRING`/`CONCAT`）；其他函数默认拒绝。

### 资源限制

- 单查询返回行数 ≤ 1000。
- 返回字段数 ≤ 50。
- 总结果字节 ≤ 1MB。
- 执行超时 10 秒。

### 可见性与审计

- 普通用户不可见完整 SQL，仅见结果摘要、图表与解读。
- `admin` 可在审计页面查看完整 SQL。
- SQL 指纹、执行摘要、用户、时间、错误码写入 `data_query_agent_db`，保留 90 天。

## 后果

- 白名单维护成本：新增表或列必须更新 YAML 真源 + 重新部署。
- 普通用户的"运行详情"页面信息量受限。
- MCP server 成为运行依赖；若课件 MCP server 不可用，需要先实现等价的 MySQL 只读 adapter。

## 关键实现约束

- 白名单、资源限制、超时通过类型化 Settings 注入。
- SQL AST 校验模块独立可测，不依赖 Prompt。
- SQL 审计表索引覆盖 `user_id`、`created_at`、`error_code`。

## 回滚

若 MCP server 不可用且无法快速实现等价 adapter，可关闭智能问数执行入口，保留 NL2SQL 生成与 AST 校验的离线能力（仅展示生成的 SQL，不执行）。
