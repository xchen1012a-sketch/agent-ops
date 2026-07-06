# KNOW-300 Data Query Knowledge And SQL

## Status

Implementation completed on 2026-07-06. Final report packaging moved to `KNOW-400-demo-report-acceptance`.

## Goal

Make the data-query assistant reproducible for MVP evidence using existing project assets: `shop_db`-style schema, wide tables, indicators, NL2SQL prompt sources, SQL whitelist/AST policy, deterministic local query results, natural-language interpretation, chart semantics, and Feishu mock evidence.

## Source Boundary

- Current `docs/homework/` now includes course data-query materials, including `AI编程_智能问数实训(课件)/shop_db_export.sql`, `06_智能问数/` data dictionary / wide-table / NL2SQL prompt materials, and a `feishu-to-dify/` sample project.
- This phase still does not claim a verified real Dify app export, real Feishu tenant callback, real DeepSeek call, or live external MySQL query.
- Project-local data-query assets are the executable truth source for this phase:
  - `agents/data-query-agent/src/data_query_agent/prompts/data_query/schema_catalog.v1.json`
  - `agents/data-query-agent/src/data_query_agent/prompts/data_query/indicators.v1.json`
  - `agents/data-query-agent/src/data_query_agent/prompts/data_query/sql_whitelist.v1.json`
  - `agents/data-query-agent/src/data_query_agent/prompts/data_query/evaluation_fixtures.v1.json`
  - `agents/data-query-agent/src/data_query_agent/domain/policies/sql_ast.py`
  - local Feishu mock flow and fake read-only query adapter.
- Any result returned from fixture data must be described as local deterministic MVP evidence, not as live MySQL output.

## Scope

- Keep `wide_orders` and `wide_order_details` as the MVP table surface.
- Align 8 standard questions with safe baseline SQL and expected local results.
- Validate baseline SQL through the existing AST/whitelist policy before execution.
- Use the fake read-only query adapter for local deterministic execution.
- Preserve SQL safety boundaries: SELECT only, whitelisted tables/columns/functions, required LIMIT, no write SQL, no system schemas, no comments/multi-statement bypass.
- Expose at least one chart semantic result for the report/demo package.
- Keep Feishu evidence as mock/local until real tenant credentials are explicitly available and verified.

## Not Doing

- No live MySQL claim without a verified `shop_db` connection and dump.
- No production MCP service governance.
- No real Feishu callback/subscription claim.
- No write SQL execution.
- No fake answer that bypasses SQL generation, SQL policy validation, and structured result evidence.

## Slice 1 Completed: Local 8-Question Fixture Execution

### Changes

- Rewrote `evaluation_fixtures.v1.json` into readable Chinese 8-question fixtures with an explicit source boundary.
- Adjusted baseline SQL so all 8 statements pass the current SQL AST/whitelist policy.
- Added `make_fixture_query_adapter()` to build a fake read-only adapter directly from the fixture catalog.
- Updated deterministic workflow generation to match exact fixture questions before falling back to the older demo SQL.
- Updated deterministic query execution to return fixture expected results by baseline SQL.
- Added readable Chinese fixture assertions and workflow chart evidence tests.
- Fixed SQL policy function-name handling so logical `AND`/`OR` are not treated as SQL functions and sqlglot date aliases remain mapped to allowed date functions.

### Evidence

- All 8 fixture baseline SQL statements passed `SqlAstPolicyValidator` with the current whitelist.
- Standard question `各渠道销售额排行` now produces:
  - case id: `T2`
  - baseline SQL over `wide_orders`
  - local fixture result rows: `app`, `web`
  - chart semantic: bar chart with `channel` as x and `total_sales` as y.

### Verification Commands

Run from `C:\Users\ahua\Desktop\agent\agents\data-query-agent`:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\data_query_agent\domain\policies\sql_ast.py src\data_query_agent\infrastructure\db\fake_query_adapter.py src\data_query_agent\workflows\state.py src\data_query_agent\workflows\nodes.py tests\unit\test_data_catalog_service.py tests\unit\test_fake_query_adapter.py tests\unit\test_data_query_workflow.py
```

Result: passed, `All checks passed!`.

```powershell
.\.venv\Scripts\python.exe -m mypy src\data_query_agent\domain\policies\sql_ast.py src\data_query_agent\infrastructure\db\fake_query_adapter.py src\data_query_agent\workflows\state.py src\data_query_agent\workflows\nodes.py tests\unit\test_data_catalog_service.py tests\unit\test_fake_query_adapter.py tests\unit\test_data_query_workflow.py
```

Result: passed, `Success: no issues found in 7 source files`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_data_catalog_service.py tests\unit\test_fake_query_adapter.py tests\unit\test_data_query_workflow.py tests\unit\test_sql_ast_policy.py -q -p no:cacheprovider --basetemp .\.pytest-basetemp-know300-slice --tb=short
```

Result: passed, `53 passed in 0.96s`.

## Remaining Work

- Final report wording and optional screenshots are tracked in `KNOW-400`.
- A production hardening phase can later decide whether the local-demo API projection should be replaced by a persisted async runner.
- Do not claim live MySQL/Feishu/Dify unless verified in that later phase.

## Slice 2 Completed: API, Web, And Feishu Mock Evidence Projection

### Changes

- Added `POST /v1/threads/{thread_id}/runs/local-demo` as an explicit local deterministic workflow evidence endpoint.
- Kept the existing persisted run creation contract unchanged: `/runs` still creates a pending run and does not expose SQL.
- Added `RunLocalDemoResponse` with source boundary, fixture id, generated SQL, policy result, local query result, answer, chart semantics, follow-ups, and node trace.
- Added Web client/types for the local-demo endpoint.
- Updated the data conversation page to display local deterministic evidence beside the streamed answer: source note, baseline SQL, result table, and a compact chart projection.
- Added API tests for owned-thread access and the standard fixture question `各渠道销售额排行`.
- Added Feishu mock flow coverage proving the same fixture chart semantics are projected into the mock card path.

### Evidence

- Standard Web/API local-demo question `各渠道销售额排行` returns:
  - source status: `local_deterministic_fixture`
  - source note: local deterministic MVP evidence only, not live MySQL/Dify/Feishu
  - fixture case id: `T2`
  - allowed SQL over `wide_orders`
  - query result rows: `app`, `web`
  - chart semantic: bar chart using `channel` and `total_sales`
  - node trace through input validation, intent, schema retrieval, SQL generation, policy check, query execution, result validation, interpretation, and audit boundary.
- Feishu mock message `各渠道销售额排行` now returns a mock chart card with the same chart semantic.

### Verification Commands

Run from `C:\Users\ahua\Desktop\agent\agents\data-query-agent`:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\data_query_agent\api\v1\schemas\runs.py src\data_query_agent\api\v1\endpoints\runs.py tests\unit\test_run_api.py tests\unit\test_feishu_mock_flow.py
```

Result: passed, `All checks passed!`.

```powershell
.\.venv\Scripts\python.exe -m mypy src\data_query_agent\api\v1\schemas\runs.py src\data_query_agent\api\v1\endpoints\runs.py tests\unit\test_run_api.py tests\unit\test_feishu_mock_flow.py
```

Result: passed, `Success: no issues found in 4 source files`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_run_api.py tests\unit\test_feishu_mock_flow.py tests\unit\test_data_query_workflow.py tests\unit\test_result_projection_service.py -q -p no:cacheprovider --basetemp .\.pytest-basetemp-know300-api-web --tb=short
```

Result: passed, `29 passed in 1.35s` with one Starlette `httpx` deprecation warning from `fastapi.testclient`.

Run from `C:\Users\ahua\Desktop\agent\agent-suite-web`:

```powershell
npm.cmd run lint
```

Result: passed.

Local runtime smoke on 2026-07-06:

- Started data-query dependencies and backend with:

```powershell
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\start-agent-runtime.ps1 -Agent data
```

Result: MySQL and Redis containers running; data-query live health passed on `http://127.0.0.1:8103`.

- `GET http://127.0.0.1:8103/openapi.json` contains `local-demo`.
- Through the Vite proxy on `http://127.0.0.1:7777`, dev auth login succeeded, data thread creation returned `201`, and `POST /api/data/v1/threads/{thread_id}/runs/local-demo` returned `200` with fixture `T2`, allowed SQL, local rows `app`/`web`, and bar chart semantics.

```powershell
npm.cmd run typecheck
```

Result: passed.

## Rollback

- Restore the previous `evaluation_fixtures.v1.json`.
- Remove `make_fixture_query_adapter()`.
- Remove fixture matching from deterministic workflow nodes.
- Restore SQL AST alias/logical-operator behavior if a stricter policy replacement is introduced.
