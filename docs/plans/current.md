# Current Phase

- Phase: `FIX-agent-ui-claude-alignment`
- Name: Align data and recruitment agent pages with Claude-style legal baseline
- Status: completed.
- Phase file: `docs/plans/phases/FIX-agent-ui-claude-alignment.md`
- Current module: `agent-suite-web` data and recruitment pages.
- Planned scope: align data-query and recruitment landing/detail page layout, message styling, scrolling, and assistant avatar behavior with the legal agent Claude-style baseline.
- Do not modify: production credentials, real Feishu configuration, global Claude/Codex configuration, or unverified external MCP/Dify services.
- External services: real Dify, Feishu, DeepSeek, and external MySQL are not claimed unless verified in the current repo/runtime.
- Current next step: wait for user review/next MVP priority.

## Current Fix: FIX-agent-ui-claude-alignment

- Baseline: legal agent detail page now uses a fixed viewport chat layout, internal conversation scrolling, subtle scrollbars, quiet assistant messages, and pending-only spinner state.
- Issue: data and recruitment pages were visually inconsistent with that baseline.
- Completed fix: data landing no longer shows main-area recents; data detail and recruitment detail use fixed internal chat scrolling; recruitment landing helper message now uses quiet Claude-style reply styling. Frontend lint/typecheck passed and browser checks passed for reachable pages.

## Previous Fix: FIX-legal-context-fixed-layout

- Root cause: legal SSE loaded conversation history for the deterministic workflow but sent only the latest question to the real stream adapter.
- Frontend issue: the legal chat page allowed the message list to grow the document height instead of scrolling inside a fixed chat viewport.
- Fix: carry bounded prior messages into the stream prompt, add unit coverage for context propagation, and constrain the legal session page to an internal scroll layout.
- Completed: legal SSE prompt now includes recent context, targeted backend/frontend checks passed, legal runtime was restarted, and a two-turn gateway SSE smoke passed with no `run.failed`.

## Previous Fix: FIX-legal-stream-dynamic-output

- Root cause: legal SSE discarded real model answer chunks and then streamed the deterministic fallback answer.
- Frontend issue: historical assistant avatar looked like an active spinner.
- Fix: forward real answer chunks, persist streamed answer when used, add safe progress thinking, and reserve spinner styling for pending generation.
- Completed: legal SSE now emits thinking delta, answer delta, completed event, and persists the streamed DeepSeek answer; history assistant avatar is no longer styled as an active spinner.

## Previous Fix: FIX-legal-deepseek-405

- Root cause: configured `base_url` is `https://platform.deepseek.com/v1`, but the API-compatible base URL should be `https://api.deepseek.com`.
- The saved API key exists and should be retained.
- Fix: update only the current legal assistant DeepSeek `base_url`.
- Completed: legal DeepSeek config now uses `https://api.deepseek.com`; SSE smoke returned 200 with answer deltas and no `HTTP 405`.

## Previous Fix: FIX-restore-api-config-entry

- API config route/page still exists at `/settings/api-config`.
- The visible sidebar entry was removed during MVP simplification.
- Restore the entry in the sidebar footer area while keeping the collapse toggle at the top.
- Completed: sidebar entry restored, route smoke passed, three API config list endpoints returned 200, frontend typecheck/lint passed.

## Previous Completed Phase: KNOW-400-demo-report-acceptance

## Current Progress: KNOW-400-demo-report-acceptance

- Source materials were refreshed against the current `docs/homework/` directory.
- The plan now recognizes the available legal courseware, Dify node cases, intelligent data-query courseware, `shop_db_export.sql`, NL2SQL prompt files, and Feishu-to-Dify sample project.
- MVP acceptance remains local/demo oriented: this project currently proves runnable local agent flows, not production external-service integration.
- Runtime smoke has verified the Web app on `http://127.0.0.1:7777`, three Agent health endpoints, dev login, and the data-query local-demo endpoint returning fixture `T2`, SQL, 2 result rows, and a bar chart semantic.

## Recent Completed Phase: KNOW-300-data-query-knowledge-sql

- Phase file: `docs/plans/phases/KNOW-300-data-query-knowledge-sql.md`
- Status: implementation completed, final report wording moved to KNOW-400.
- Result: local deterministic 8-question fixture execution, SQL policy validation, fake read-only adapter, local-demo API projection, Web SQL/table/chart evidence, and Feishu mock chart-card semantics.
- Verification: ruff passed, targeted mypy passed, data-query pytest slice passed with `29 passed`, and `agent-suite-web` lint/typecheck passed.

## Recent Completed Phase: KNOW-200-recruitment-conversation-workflow

- Phase file: `docs/plans/phases/KNOW-200-recruitment-conversation-workflow.md`
- Status: completed.
- Result: recruitment assistant UI simplified into a Claude-style conversation flow; versioned MVP rules, structured analysis, fairness protected-attribute boundaries, report evidence, and frontend match summary were added.
- Verification: ruff passed, targeted mypy passed, recruitment pytest slice passed with `35 passed`, and `agent-suite-web` typecheck passed.

## Recent Completed Phase: KNOW-100-legal-knowledge-assistant

- Phase file: `docs/plans/phases/KNOW-100-legal-knowledge-assistant.md`
- Status: backend completed.
- Result: transparent course-template legal knowledge seed, deterministic retrieval fallback, explicit no-source/mock retrieval paths, and legal agent unit-test evidence.

## Recent Completed Phase: KNOW-000-source-inventory

- Phase file: `docs/plans/phases/KNOW-000-source-inventory.md`
- Status: completed; source boundary refreshed during KNOW-400.
- Result: established the source inventory, required knowledge files, missing materials, and no-fabrication boundaries for legal, recruitment, and data-query agents.

## Recent Fixes

- `RECRUIT-270-claude-chat-ui`: recruitment assistant simplified into a conversation entry and task conversation flow.
- `FIX-login-api-no-response`: local browser login now uses same-origin Vite dev-auth on `http://127.0.0.1:7777/api/auth/*`; login and `/me` both return 200.
