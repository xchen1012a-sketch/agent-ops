# auth-service (课程 MVP)

为 `enterprise-agent-suite` 前端提供最小独立认证后端,实现 `docs/contracts/frontend-backend-api.md` §2 的全部 5 个端点:

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET  /api/auth/me`
- `POST /api/auth/change-password`

## 适用范围

- 课程 MVP:内存用户、JWT access + HttpOnly refresh cookie。
- 不持久化(进程重启后密码改动丢失)、无注册接口、无邮件验证。
- 生产部署前需替换:JWT secret、cookie domain、TLS、用户持久化。

## 启动

```bash
cd agents/auth-service
python -m venv .venv
. .venv/Scripts/activate    # Windows bash
pip install -e .
cp .env.example .env         # 按需修改
uvicorn auth_service.main:app --port 8081 --reload
```

默认端口 **8081**(匹配 `agent-suite-web/vite.config.ts` 的 `/api/auth` 代理目标 `http://localhost:8081`)。

## 内置用户

| 邮箱 | 密码 | 角色 |
|---|---|---|
| `admin@suite.local` | `Admin@123` | admin |
| `user@suite.local` | `User@12345` | user |

## 与前端的关系

- 前端 `agent-suite-web/src/api/auth.ts` 直接调用 `/api/auth/*`。
- vite dev 默认把 `/api/auth` 代理到 `http://localhost:8081`;无需改前端 env。
- 若启用 `VITE_ENABLE_DEV_AUTH=true`,前端会用内置 `dev-auth-plugin` 而非本服务——联调真实后端时**不要**启用该开关。

## Cookie

- refresh token 走 HttpOnly cookie,`Path=/api/auth`,`SameSite=Lax`。
- dev 下 `secure=False`(HTTP);生产需在 TLS 后切 `secure=True`。
