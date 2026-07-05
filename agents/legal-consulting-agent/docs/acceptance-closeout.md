# Legal Agent acceptance closeout

> Date: 2026-07-05  
> Scope: `agents/legal-consulting-agent` local planned scope closeout  
> Status: local module acceptance passed; external-service integration remains deferred.

## 1. Scope accepted

The legal consulting Agent is accepted for the current local planned scope:

- Data layer:
  - user mirror
  - legal categories
  - sessions and messages
  - agent/node audit records
  - consultation records
  - feedbacks
  - high-risk reviews
  - prompt versions
  - knowledge material metadata
- Workflow layer:
  - deterministic LangGraph workflow
  - audit mapping
  - workflow runner boundary
  - prompt template loading
  - prompt output validation
  - prompt-backed classification / generation / risk-check assembly
- API layer:
  - session creation
  - question answering
  - SSE event contract
  - message history
  - feedback
  - high-risk review enqueue and admin resolution
  - Markdown report projection
  - consultation record history
  - workflow cancel/retry preview

## 2. Verification evidence

Commands were executed from `agents/legal-consulting-agent`.

Because the default sandbox cannot write to the user-level `uv` cache and user Temp directory, verification used module-local paths:

```powershell
$env:UV_CACHE_DIR=(Resolve-Path .\.uv-cache).Path
$env:TMP=(Resolve-Path .\.tmp).Path
$env:TEMP=(Resolve-Path .\.tmp).Path
```

| Check | Command | Result |
|---|---|---|
| Ruff lint | `uv run ruff check src tests` | Passed: `All checks passed!` |
| Ruff format | `uv run ruff format --check src tests` | Passed: `105 files already formatted` |
| MyPy | `uv run mypy src` | Passed: `Success: no issues found in 72 source files` |
| Pytest + coverage | `uv run pytest --cov=legal_consulting_agent -q -p no:cacheprovider` | Passed: `133 passed`, coverage `90%` |
| Alembic heads | `uv run alembic heads` | Passed: single head `ceeb31ed5ac6 (head)` |
| OpenAPI smoke | `create_app().openapi()` | Passed: generated `28` paths |

OpenAPI path count includes both direct module prefix `/v1/...` and gateway prefix `/api/legal/v1/...`.

## 3. Deferred / not verified

| Item | Status | Reason / next owner |
|---|---|---|
| `alembic current` / live DB revision | Not verified | Current environment has no configured database URL. |
| Real MySQL `upgrade -> downgrade -> upgrade` for latest state | Not rerun | No new DB migrations were added after the accepted data-layer migrations. |
| Real DeepSeek call | Deferred | Requires confirmed credentials and adapter integration phase. |
| Real Qdrant / BGE / reranker retrieval | Deferred | Requires legal knowledge samples and local service fixtures. |
| Token-level LLM streaming | Deferred | Current SSE endpoint freezes event contract, not token streaming. |
| PDF / object-storage report export | Deferred | Current report is synchronous Markdown projection only. |
| Full frontend E2E | Deferred | Frontend is being developed in parallel by another AI. |
| Docker Compose end-to-end run | Deferred | Belongs to OPS-600 / QA-700 integration phases. |

## 4. Closeout decision

The legal Agent should be treated as **module-complete for local planned scope**.

Remaining work should not reopen `LEGAL-100` by default. Track it under:

- `OPS-600` for compose / gateway / local infrastructure integration.
- `QA-700` for cross-module regression and E2E verification.
- `REPORT-800` for screenshots, report writing, and demo evidence.
- A future integration slice if real DeepSeek / Qdrant / BGE fixtures are provided.

## 5. Safe handoff notes

- Do not modify legal data migrations unless a new schema requirement is explicitly approved.
- Do not connect real DeepSeek, Qdrant, BGE, or production MySQL without user confirmation.
- Keep frontend integration through public OpenAPI/SSE only.
- Do not let the legal Agent import recruitment or data-query modules.
