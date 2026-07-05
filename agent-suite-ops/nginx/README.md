# Nginx reverse proxy configuration

Place the upstream-agnostic routing configuration here when the OPS-620 nginx
service lands. Routes per `agent-suite-ops/docs/runbooks/deployment-design.md` §7:

- `/`           -> `suite-web`
- `/api/legal`  -> `legal-agent:8101`
- `/api/recruitment` -> `recruitment-agent:8102`
- `/api/data`   -> `data-query-agent:8103`

SSE rules:
- Disable `proxy_buffering`.
- Set `X-Accel-Buffering: no` on streaming responses.
- Use `proxy_read_timeout` >= the longest agent run.
