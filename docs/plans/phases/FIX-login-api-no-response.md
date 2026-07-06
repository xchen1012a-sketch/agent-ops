# FIX-login-api-no-response

## Status

- Status: completed.
- Current phase: completed.
- Trigger: Web login reports no login API response after local `develop` startup.

## Symptom

User cannot log in from the local Web app. The reported behavior is that the login API has no response.

## Initial Evidence

- Current local frontend uses `VITE_ENABLE_DEV_AUTH=true`, so `/api/auth/login` should be handled by `agent-suite-web/dev-auth-plugin.ts` through the Vite dev server.
- Frontend is running on `http://127.0.0.1:7777/`.
- Business Agent health checks pass through the frontend proxy, so the Vite server itself is reachable.
- Direct API smoke passed before fix when using the current Vite origin: `POST http://127.0.0.1:7777/api/auth/login` returned 200.
- Browser reproduction failed because the frontend runtime requested `POST http://127.0.0.1:5666/api/auth/login`, which returned `ERR_CONNECTION_REFUSED`.

## Impact Scope

- Primary: `agent-suite-web` authentication flow, Vite dev-auth middleware, auth API client.
- Secondary: local startup smoke and MVP browser route smoke.
- Not in scope unless proven necessary: real `auth-service`, production authentication design, database schema, external services.

## Do Not Do

- Do not read or print real `.env` secrets.
- Do not change global Codex/Claude configuration.
- Do not connect production services.
- Do not rewrite the auth architecture.
- Do not alter unrelated Agent business flows.

## Phases

### Phase 1: Reproduce and isolate

- Send the smallest direct request to `POST http://127.0.0.1:7777/api/auth/login`.
- Compare with frontend auth client base URL and Vite dev-auth route matching.
- Inspect Vite stdout/stderr for request handling or compile errors.

Verification:

- Record request URL, payload shape, status code/body or timeout/error.

### Phase 2: Root cause and minimal fix

- If route mismatch is confirmed, fix dev-auth middleware or frontend auth path at the source.
- If the Vite process is stale, restart through the existing local startup path.
- If auth-service is required instead of dev-auth, update local run instructions rather than guessing credentials.

Verification:

- Direct login API request returns an access token.
- Login page can complete the auth flow.

### Phase 3: Regression check

- Run the smallest relevant frontend unit test or add one if the route bug is code-level.
- Re-run frontend auth smoke and current MVP health smoke.

Verification:

- `POST /api/auth/login` succeeds.
- `GET /api/auth/me` succeeds with the returned token.
- Frontend page remains reachable.

## Stop Conditions

- The failure cannot be reproduced from direct API or browser flow.
- Fix requires changing real auth-service credentials or production auth behavior.
- Logs reveal sensitive secrets that must be handled manually.

## Rollback

- Revert touched frontend auth/dev server files.
- Restore `docs/plans/current.md` to `MVP-003-prune-hidden-features`.
- Restart Vite if the running process is stale.

## Root Cause

`agent-suite-web/.env` had `VITE_API_BASE_URL=http://127.0.0.1:5666`, but the current local Vite dev server was started on `http://127.0.0.1:7777`.

With `VITE_ENABLE_DEV_AUTH=true`, the mock auth endpoints are mounted inside the Vite dev server. Because the browser used the stale `5666` base URL, login bypassed the running dev server and never reached `dev-auth-plugin.ts`.

## Fix

- Updated local ignored config `agent-suite-web/.env`: `VITE_API_BASE_URL=` so frontend API calls use same-origin Vite proxy/dev-auth.
- Restarted the Vite dev server so it reloaded the `.env` value.
- No source code or backend auth behavior was changed.

## Verification Record 2026-07-06

- Direct auth smoke: `POST http://127.0.0.1:7777/api/auth/login` returned 200 with `dev-auth-token.dev-admin`.
- Auth profile smoke: `GET http://127.0.0.1:7777/api/auth/me` returned 200 with admin profile.
- Agent proxy smoke:
  - `GET http://127.0.0.1:7777/api/legal/v1/health/live` returned 200.
  - `GET http://127.0.0.1:7777/api/recruitment/v1/health/live` returned 200.
  - `GET http://127.0.0.1:7777/api/data/v1/health/live` returned 200.
- Browser login smoke with headless Chrome:
  - Login form submitted `POST http://127.0.0.1:7777/api/auth/login` and received 200.
  - Follow-up `GET http://127.0.0.1:7777/api/auth/me` received 200.
  - Browser reached `http://127.0.0.1:7777/legal/sessions`.
- Remaining warning: Vue logs `<Suspense> slots expect a single root node`; it did not block login and is outside this fix scope.
