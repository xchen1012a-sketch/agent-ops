# syntax=docker/dockerfile:1.7
#
# Multi-stage Dockerfile for agent-suite-web.
# Build artifacts are produced under /app/dist and served via nginx in the
# runtime stage. The runtime image is non-root and includes a HEALTHCHECK.
# Aligned with agent-suite-ops/docs/standards/.

FROM node:22-alpine AS builder
WORKDIR /app

ENV CI=1 \
    NODE_OPTIONS='--max-old-space-size=2048'

COPY package.json pnpm-lock.yaml .npmrc* pnpm-workspace.yaml ./
RUN npm install -g pnpm@11.8.0 \
    && pnpm install --frozen-lockfile --ignore-scripts

COPY . .
RUN pnpm typecheck && pnpm build

FROM nginx:1.27-alpine AS runtime

RUN addgroup -g 1001 -S app && adduser -u 1001 -S -G app app

COPY nginx /etc/nginx/conf.d
COPY --from=builder /app/dist /usr/share/nginx/html

RUN chown -R app:app /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown app:app /var/run/nginx.pid

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1/health/live || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
