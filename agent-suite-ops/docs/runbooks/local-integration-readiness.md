# Local integration readiness runbook

> Scope: enterprise-agent-suite local integration preparation.  
> This runbook is a checklist, not an instruction to connect production services.

## 1. Preconditions

Before running full local integration:

- Frontend current slice is complete and committed or clearly isolated.
- Data Query Agent `DATA-300` planned local scope is complete.
- Recruitment Agent `RECRUIT-240/250/260` planned local scope is complete.
- Legal Agent local scope is accepted.
- `.env` is created from `agent-suite-ops/.env.example` with local-only secrets.
- No real production database, Feishu tenant, DeepSeek key, or user data is used unless explicitly confirmed.

## 2. Workspace safety check

Run from repository root:

```powershell
git status --short
```

Expected:

- Changes are grouped by module.
- No unrelated parallel AI changes are mixed into the current integration commit.
- No real `.env`, secrets, archives, or generated build outputs are staged.

## 3. Module quality gates

Run module gates before compose integration.

| Module | Commands |
|---|---|
| Legal Agent | `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src`; `uv run pytest --cov=legal_consulting_agent -q`; `uv run alembic heads` |
| Recruitment Agent | `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src`; `uv run pytest --cov=recruitment_assistant_agent -q`; `uv run alembic heads` |
| Data Query Agent | `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src`; `uv run pytest --cov=data_query_agent -q`; `uv run alembic heads` |
| Web | `pnpm typecheck`; `pnpm lint`; `pnpm format:check`; `pnpm test`; `pnpm build` |

Record unrun checks as **not verified**.

## 4. Compose dry run

From `agent-suite-ops`:

```powershell
docker compose config
```

Expected:

- Compose parses successfully.
- No image uses `latest`.
- No service mounts a production path.
- No environment value contains a real secret in committed files.

## 5. Local dependency startup

Start infrastructure first:

```powershell
docker compose up mysql redis qdrant bge-embedding bge-reranker
```

Check:

- MySQL is healthy.
- Redis responds to ping.
- Qdrant health endpoint is available.
- BGE services are either healthy or explicitly marked not verified.

## 6. Service startup order

Then start services:

```powershell
docker compose up legal-agent recruitment-agent data-query-agent suite-web suite-ops-nginx
```

Expected route prefixes:

| Route | Service |
|---|---|
| `/api/legal/v1/health/live` | legal-agent |
| `/api/recruitment/v1/health/live` | recruitment-agent |
| `/api/data/v1/health/live` | data-query-agent |
| `/` | suite-web |

## 7. Smoke checklist

| Smoke | Expected |
|---|---|
| Web loads | Main shell renders without console errors |
| Legal health | 200 live; ready depends on local DB config |
| Recruitment health | 200 live; ready depends on local DB config |
| Data health | 200 live; ready depends on local DB config |
| Legal question path | Creates or previews run using local boundaries |
| Recruitment task path | Creates task/material using local boundaries |
| Data query path | Runs fake or fixture-backed query, not production DB |
| Nginx route isolation | Stopping one Agent does not break other routes |

## 8. Failure diagnostics

| Symptom | First check |
|---|---|
| Gateway 502 | target service container health and route prefix |
| Agent ready 503 | database URL, migration state, Redis URL |
| SSE disconnects | Nginx proxy buffering and timeout settings |
| Data query refuses SQL | SQL policy decision and whitelist config |
| Recruitment report blocked | admin review status and fairness checks |
| Legal answer has no citation | RAG service / knowledge source availability |

## 9. Stop / cleanup

Use explicit compose shutdown:

```powershell
docker compose down
```

Do not delete volumes unless the user explicitly confirms data cleanup.

If volume cleanup is confirmed:

```powershell
docker compose down -v
```

## 10. Evidence to save

- `docker compose config` output summary.
- `docker compose ps` health status.
- Health endpoint responses.
- Module quality gate outputs.
- Screenshots for report/demo.
- Known not-verified list.
