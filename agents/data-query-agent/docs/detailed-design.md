# DATA-310 智能问数 Agent 详细设计

> 状态：DESIGN-002 子阶段设计产出；FOUND-010 已建立工程基础，等待 DATA-300/DATA-330 业务实现授权。
> 真源：本文件 + `specification.md` + `adr/0007-unified-auth.md`、`adr/0010-data-query-sql-safety.md`、`adr/0011-deployment-and-database-permissions.md`。
> 数据库结构以课件 `shop_db_export.sql` 为最终真源；本文件给出推断式字典，DATA-320 启动时与课件 `shop_db` 实际表对齐。

## 1. 数据范围

- 数据库：`shop_db`（独立只读账号 `data_query_reader`）。
- 业务场景：全品类 B2C 电商。
- 数据规模：约 5 万订单、14.9 万订单明细（课件基准）。
- 主要能力：汇总、排行、筛选、趋势、占比、同比、环比、退款率、毛利率、客单价、日均/周均销售额、复购标记。

## 2. 数据字典（推断式，以 shop_db_export.sql 为准）

### 2.1 维度表（8 张）

| 表 | 含义 | 关键字段 |
|---|---|---|
| `dim_date` | 日期 | `date_key`, `date`, `year`, `month`, `week`, `is_weekend`, `is_holiday`, `holiday_name` |
| `dim_time` | 时间 | `time_key`, `hour`, `minute` |
| `dim_customer` | 客户 | `customer_key`, `customer_id`, `name`, `tier`（普通/金卡/钻石）, `region`（华东/华南/华北/...） |
| `dim_product` | 商品 | `product_key`, `product_id`, `name`, `brand`, `category`, `subcategory` |
| `dim_category` | 品类 | `category_key`, `category`, `parent_category` |
| `dim_channel` | 销售渠道 | `channel_key`, `channel_name`（官网/APP/小程序/第三方） |
| `dim_payment` | 支付方式 | `payment_key`, `payment_method`（支付宝/微信/银行卡/...） |
| `dim_region` | 区域 | `region_key`, `province`, `city`, `region` |

### 2.2 事实表（2 张）

| 表 | 含义 | 关键字段 |
|---|---|---|
| `fact_orders` | 订单事实 | `order_id`, `customer_key`, `product_key`, `channel_key`, `payment_key`, `date_key`, `time_key`, `quantity`, `unit_price`, `total_amount`, `is_refunded`, `refund_amount` |
| `fact_order_details` | 订单明细 | `detail_id`, `order_id`, `product_key`, `quantity`, `unit_price`, `discount`, `subtotal` |

### 2.3 宽表（2 张）

| 表 | 含义 | 关键字段 |
|---|---|---|
| `wide_orders` | 订单宽表 | denormalized，约 5 万行 |
| `wide_order_details` | 订单明细宽表 | denormalized，约 14.9 万行；含 `holiday_name`, `gross_profit`, `is_repeat_purchase`, `region`, `category`, `brand`, `channel`, `payment_method` 等 |

DATA-320 启动时执行 `DESCRIBE` 与 `INFORMATION_SCHEMA.COLUMNS` 实测对齐。

## 3. 指标字典

文件 `/app/data/prompts/data-query/indicators.yaml`：

```yaml
version: v1
indicators:
  - name: total_sales
    formula: SUM(total_amount)
    description: 总销售额
    applicable_tables: [fact_orders, wide_orders]
  - name: total_quantity
    formula: SUM(quantity)
    description: 总销量
  - name: avg_order_value
    formula: SUM(total_amount) / COUNT(DISTINCT order_id)
    description: 客单价
  - name: refund_rate
    formula: SUM(CASE WHEN is_refunded=1 THEN 1 ELSE 0 END) / COUNT(*)
    description: 退款率
    applicable_tables: [fact_orders, wide_orders]
  - name: gross_margin
    formula: SUM(gross_profit) / SUM(total_amount)
    description: 毛利率
    applicable_tables: [wide_order_details]
  - name: daily_avg_sales
    formula: SUM(total_amount) / COUNT(DISTINCT date_key)
    description: 日均销售额
  - name: weekly_avg_sales
    formula: SUM(total_amount) / COUNT(DISTINCT YEARWEEK(date_key))
    description: 周均销售额
  - name: repeat_purchase_rate
    formula: COUNT(DISTINCT CASE WHEN is_repeat_purchase=1 THEN customer_id END) / COUNT(DISTINCT customer_id)
    description: 复购率
  - name: channel_share
    formula: SUM(total_amount) BY channel / SUM(total_amount) OVER()
    description: 渠道占比
time_semantics:
  relative_keywords:
    last_month: "YEAR(date)=YEAR(CURRENT_DATE - INTERVAL 1 MONTH) AND MONTH(date)=MONTH(CURRENT_DATE - INTERVAL 1 MONTH)"
    last_week: "YEARWEEK(date)=YEARWEEK(CURRENT_DATE - INTERVAL 7 DAY)"
    this_year: "YEAR(date)=YEAR(CURRENT_DATE)"
  yoy: # 同比
    template: "current / (same_period_last_year) - 1"
  mom: # 环比
    template: "current / (last_month) - 1"
```

## 4. SQL 策略 YAML（白名单）

文件 `/app/data/prompts/data-query/sql-whitelist.yaml`：

```yaml
version: v1
allowed_tables:
  - dim_date
  - dim_time
  - dim_customer
  - dim_product
  - dim_category
  - dim_channel
  - dim_payment
  - dim_region
  - fact_orders
  - fact_order_details
  - wide_orders
  - wide_order_details
allowed_columns:
  # DATA-320 启动时从 INFORMATION_SCHEMA.COLUMNS 全量导入
  # 此处仅列关键示例
  fact_orders: [order_id, customer_key, product_key, channel_key, payment_key, date_key, time_key, quantity, unit_price, total_amount, is_refunded, refund_amount]
  wide_order_details: [detail_id, order_id, customer_id, product_id, product_name, brand, category, subcategory, channel, payment_method, region, province, city, date, quantity, unit_price, total_amount, gross_profit, is_refunded, is_repeat_purchase, holiday_name]
allowed_functions:
  aggregate: [SUM, COUNT, AVG, MIN, MAX, COUNT_DISTINCT]
  date: [DATE, DATE_FORMAT, YEAR, MONTH, DAY, YEARWEEK, WEEKDAY, NOW, CURRENT_DATE, DATE_ADD, DATE_SUB, INTERVAL]
  string: [SUBSTRING, CONCAT, LENGTH, UPPER, LOWER, TRIM]
  numeric: [ROUND, ABS, COALESCE, IFNULL]
  control: [CASE, IF]
forbidden_keywords:
  - UNION
  - INTO OUTFILE
  - INTO DUMPFILE
  - LOAD_FILE
  - SLEEP
  - BENCHMARK
  - INFORMATION_SCHEMA
  - MYSQL
  - PERFORMANCE_SCHEMA
  - SYS
allowed_clauses:
  - SELECT
  - FROM
  - WHERE
  - GROUP BY
  - HAVING
  - ORDER BY
  - LIMIT
  - JOIN
  - LEFT JOIN
  - INNER JOIN
  - WITH  # CTE
  - AS
forbidden_clauses:
  - INSERT
  - UPDATE
  - DELETE
  - DROP
  - ALTER
  - CREATE
  - TRUNCATE
  - GRANT
  - REVOKE
  - CALL        # 存储过程
  - SET         # 用户变量
limits:
  max_rows: 1000
  max_fields: 50
  max_bytes: 1048576
  execution_timeout_seconds: 10
  statement_count: 1   # 单语句
```

## 5. MCP 契约

### 5.1 工具 schema

```json
{
  "name": "execute_sql",
  "description": "Execute a validated SELECT SQL on shop_db read-only connection",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sql": { "type": "string", "description": "Validated SELECT SQL" },
      "max_rows": { "type": "integer", "default": 1000, "maximum": 1000 },
      "timeout_seconds": { "type": "integer", "default": 10, "maximum": 10 }
    },
    "required": ["sql"]
  }
}
```

### 5.2 错误响应

| MCP error code | 含义 |
|---|---|
| `SQL_POLICY_VIOLATION` | 不在白名单 |
| `SQL_PARSE_FAILED` | AST 解析失败 |
| `SQL_EXECUTION_TIMEOUT` | 执行超时 |
| `SQL_RESULT_TOO_LARGE` | 结果超字节/行数上限 |
| `DB_CONNECTION_FAILED` | shop_db 不可连接 |

## 6. 运行态数据库（data_query_agent_db）ER

```text
User (mirror) ─< Session ─< Message
              ├─< QueryRun ─< NodeRun
              │       └─< SqlAudit
              ├─< Feedback
              └─< FollowupSuggestion

AdminUser ─< PromptVersion
```

### 关键表

```sql
CREATE TABLE sessions (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  public_id CHAR(36) NOT NULL UNIQUE,
  user_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(200),
  created_at DATETIME(6) NOT NULL,
  INDEX idx_sessions_user (user_id, created_at DESC)
);

CREATE TABLE query_runs (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  public_id CHAR(36) NOT NULL UNIQUE,
  thread_id CHAR(36) NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  status ENUM('pending','running','success','failed','retrying','canceled') NOT NULL,
  question TEXT NOT NULL,
  generated_sql TEXT,                  -- 完整 SQL（admin 可见）
  sql_fingerprint CHAR(64),            -- SHA-256 of normalized SQL
  executed_at DATETIME(6),
  duration_ms INT,
  row_count INT,
  error_code VARCHAR(64),
  prompt_version VARCHAR(32) NOT NULL,
  rule_version VARCHAR(32) NOT NULL,
  started_at DATETIME(6) NOT NULL,
  finished_at DATETIME(6),
  INDEX idx_runs_thread (thread_id, started_at DESC),
  INDEX idx_runs_status (status)
);

CREATE TABLE sql_audits (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  query_run_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  sql_fingerprint CHAR(64) NOT NULL,
  sql_summary VARCHAR(500),            -- 脱敏摘要，普通用户可见
  policy_decision ENUM('allowed','blocked') NOT NULL,
  blocked_reason VARCHAR(200),
  row_count INT,
  result_summary VARCHAR(500),         -- e.g. "Total sales: ¥1,234,567"
  created_at DATETIME(6) NOT NULL,
  expires_at DATETIME(6) NOT NULL,      -- created_at + 90 days
  CONSTRAINT fk_audit_run FOREIGN KEY (query_run_id) REFERENCES query_runs(id),
  INDEX idx_audit_user_time (user_id, created_at DESC),
  INDEX idx_audit_expires (expires_at)
);
```

`sql_audits.expires_at` 由定时任务清理（90 天后归档/删除）。

## 7. API Schema

### 7.1 提问

```http
POST /v1/threads/{thread_id}/runs
{ "question": "上个月总销售额多少" }

202 Accepted
{ "run_id": "uuid", "thread_id": "uuid", "status": "pending" }
```

### 7.2 SSE 事件

```text
run.started
node.started (input_validation)
node.started (intent_classify)
node.started (schema_retrieval)
node.started (sql_generate)         # message.delta: "正在生成查询..."
node.started (sql_policy_check)
node.completed (sql_policy_check)   # allowed
node.started (mcp_execute)          # tool.started / tool.completed
node.started (result_validate)
node.started (interpret)
run.completed
  data: {
    "answer": "上个月总销售额为 ¥1,234,567",
    "table": { "columns": ["total_sales"], "rows": [["1234567.00"]] },
    "chart": { "type": null, "reason": "single value, no chart" },
    "followups": ["各渠道销售额排行", "上月环比变化"]
  }
```

普通用户：响应**不含** `sql`，仅含 `answer`、`table`、`chart`、`followups`。

### 7.3 admin SQL 审计

```http
GET /v1/admin/sql-audit?page=1&size=20&user_id=&from=&to=

200 OK
{
  "items": [
    {
      "audit_id": "...",
      "user_id": "...",
      "question_summary": "上个月总销售额",
      "sql": "SELECT SUM(total_amount) FROM wide_orders WHERE ...",
      "policy_decision": "allowed",
      "row_count": 1,
      "result_summary": "Total sales: ¥1,234,567",
      "created_at": "..."
    }
  ]
}
```

## 8. LangGraph 节点 I/O

| 节点 | 输入 | 输出 | 失败语义 |
|---|---|---|---|
| `input_validation` | question | `safe_question` | 含禁用词 → `INPUT_BLOCKED` |
| `intent_classify` | safe_question | `is_data_query: bool`, `intent` | 非数据问题 → 跳过到 `polite_refusal` |
| `schema_retrieval` | intent + history | `relevant_tables[]`, `relevant_indicators[]` | 无匹配 → `interpret_no_data` |
| `sql_generate` | intent + schema + indicators + history | `sql_candidate` + `explanation` | LLM 超时 → 重试 3 次 |
| `sql_policy_check` | sql_candidate | `validated_sql` 或 `policy_violation` | 违反 → `SQL_POLICY_VIOLATION`，不执行 |
| `mcp_execute` | validated_sql | `result_set` + `row_count` + `duration_ms` | 超时/过大 → 不可恢复 |
| `result_validate` | result_set + intent | `is_complete: bool`, `missing_dims` | 不完整 → 回到 `sql_generate`（最多 1 次） |
| `interpret` | result + intent + question | `answer_text` + `chart_semantic` | LLM 超时 → 重试 2 次 |
| `persist_audit` | 全部 | `audit_id` | DB 不可用 → 重试 3 次 |
| `polite_refusal` | n/a | 友好拒答 + 引导 | n/a |

State Schema：

```python
class DataQueryState(TypedDict):
    thread_id: str
    user_id: int
    question: str
    safe_question: Optional[str]
    is_data_query: bool
    intent: Optional[str]
    relevant_tables: list[str]
    relevant_indicators: list[dict]
    sql_candidate: Optional[str]
    validated_sql: Optional[str]
    policy_violation: Optional[str]
    result_set: Optional[list[dict]]
    row_count: Optional[int]
    is_complete: bool
    answer_text: Optional[str]
    chart_semantic: Optional[dict]
    followups: list[str]
    error_code: Optional[str]
    prompt_version: str
    rule_version: str
```

## 9. 课件 8 题基准 SQL

| ID | 问题 | 基准 SQL（示例） |
|---|---|---|
| T1 | 上个月总销售额多少 | `SELECT SUM(total_amount) FROM wide_orders WHERE YEAR(date)=YEAR(CURRENT_DATE - INTERVAL 1 MONTH) AND MONTH(date)=MONTH(CURRENT_DATE - INTERVAL 1 MONTH)` |
| T2 | 各渠道销售额排行 | `SELECT channel, SUM(total_amount) AS total FROM wide_orders GROUP BY channel ORDER BY total DESC` |
| T3 | 手机品类卖得最好的 5 个品牌 | `SELECT brand, SUM(total_amount) AS total FROM wide_order_details WHERE category='手机' GROUP BY brand ORDER BY total DESC LIMIT 5` |
| T4 | 华东区金卡用户买了多少钱 | `SELECT SUM(total_amount) FROM wide_orders WHERE region='华东' AND customer_tier='金卡'` |
| T5 | 今年每个月销售额趋势 | `SELECT MONTH(date) AS m, SUM(total_amount) AS total FROM wide_orders WHERE YEAR(date)=YEAR(CURRENT_DATE) GROUP BY m ORDER BY m` |
| T6 | 哪个支付方式用的人最多 | `SELECT payment_method, COUNT(DISTINCT customer_id) AS cnt FROM wide_orders GROUP BY payment_method ORDER BY cnt DESC LIMIT 1` |
| T7 | 退款率最高的品类是哪些 | `SELECT category, SUM(CASE WHEN is_refunded=1 THEN 1 ELSE 0 END)/COUNT(*) AS rate FROM wide_order_details GROUP BY category ORDER BY rate DESC LIMIT 5` |
| T8 | 周末和工作日哪个卖得多 | `SELECT CASE WHEN DAYOFWEEK(date) IN (1,7) THEN 'weekend' ELSE 'weekday' END AS t, SUM(total_amount) FROM wide_orders GROUP BY t` |

实际基准 SQL 在 DATA-310 阶段与课件对齐；上面仅作示例。

## 10. 扩展评测集（草案）

最少 30 题扩展：

- 10 题 TopN / 排行（不同维度组合）
- 5 题 同比 / 环比
- 5 题 占比 / 分布
- 5 题 趋势
- 5 题 安全攻击（注入、写操作、系统表、UNION、超时）

期望执行正确率 ≥ 95%；安全攻击拦截率 100%。

## 11. 错误码

| 错误码 | HTTP | 含义 |
|---|---|---|
| `INPUT_BLOCKED` | 422 | 含禁用词 |
| `NON_DATA_QUERY` | 200 | 非数据问题，友好拒答 |
| `SQL_POLICY_VIOLATION` | 422 | 白名单/AST 校验失败 |
| `SQL_PARSE_FAILED` | 422 | AST 解析失败 |
| `SQL_EXECUTION_TIMEOUT` | 504 | 执行超时 |
| `SQL_RESULT_TOO_LARGE` | 422 | 结果超限 |
| `LLM_TIMEOUT` | 504 | DeepSeek 超时 |
| `MCP_UNAVAILABLE` | 503 | MCP server 不可用 |
| `DB_CONNECTION_FAILED` | 503 | shop_db 不可连 |
| `RATE_LIMITED` | 429 | 限流 |
| `AUTH_REQUIRED` | 401 | 未登录 |
| `AUTH_FORBIDDEN` | 403 | 普通用户访问 admin 资源 |

## 12. 验收

- 课件 8 题 100% 通过（执行结果与基准 SQL 一致）。
- 扩展评测集 ≥ 95% 执行正确率。
- 安全攻击集 100% 拦截。
- 普通用户响应中无 `sql` 字段；admin 审计页可见完整 SQL。
- 多轮追问不会串用户/串会话。
- 模拟 MCP 故障 → 503 `MCP_UNAVAILABLE`，UI 降级。
- 审计 90 天保留 + 过期清理任务可验证。

## 13. 飞书测试租户

推迟到 FEISHU-500 阶段对齐。首期专注 Web 端。
