import type { IncomingMessage, ServerResponse } from 'node:http';
import type { Plugin } from 'vite';

interface DevUser {
  user_id: string;
  public_id: string;
  email: string;
  display_name: string;
  role: 'admin' | 'user';
}

const DEV_USERS: DevUser[] = [
  {
    user_id: 'dev-admin',
    public_id: '00000000-0000-4000-8000-000000000001',
    email: 'admin@example.com',
    display_name: '本地管理员',
    role: 'admin',
  },
  {
    user_id: 'dev-user',
    public_id: '00000000-0000-4000-8000-000000000002',
    email: 'user@example.com',
    display_name: '本地用户',
    role: 'user',
  },
];

const AUTH_TOKEN_PREFIX = 'dev-auth-token';

export function createDevAuthPlugin(prefix: string): Plugin {
  const normalizedPrefix = normalizePrefix(prefix);

  return {
    name: 'agent-suite-dev-auth',
    configureServer(server) {
      server.middlewares.use(normalizedPrefix, async (req, res, next) => {
        const method = req.method?.toUpperCase() ?? 'GET';
        const path = new URL(req.url ?? '/', 'http://localhost').pathname;

        if (method === 'POST' && path === '/login') {
          await handleLogin(req, res);
          return;
        }
        if (method === 'GET' && path === '/me') {
          handleProfile(req, res);
          return;
        }
        if (method === 'POST' && (path === '/refresh' || path === '/logout')) {
          sendJson(res, 200, path === '/refresh' ? createSession(DEV_USERS[0]) : { ok: true });
          return;
        }

        next();
      });
    },
  };
}

function normalizePrefix(prefix: string): string {
  const trimmed = prefix.trim();
  if (!trimmed) return '/api/auth';
  return trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
}

async function handleLogin(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const body = await readJsonBody(req).catch(() => null);
  const email = typeof body?.email === 'string' ? body.email.trim().toLowerCase() : '';
  const password = typeof body?.password === 'string' ? body.password : '';
  const user = DEV_USERS.find((item) => item.email === email);

  if (!user || password.length < 8) {
    sendJson(res, 401, {
      error_code: 'AUTH_INVALID_CREDENTIALS',
      message: '账号或密码不正确',
    });
    return;
  }

  sendJson(res, 200, createSession(user));
}

function handleProfile(req: IncomingMessage, res: ServerResponse): void {
  const token = readBearerToken(req);
  const user = findUserByToken(token) ?? DEV_USERS[0];
  sendJson(res, 200, createProfile(user));
}

function createSession(user: DevUser) {
  return {
    access_token: `${AUTH_TOKEN_PREFIX}.${user.user_id}`,
    expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
  };
}

function createProfile(user: DevUser) {
  const now = new Date().toISOString();
  return {
    user_id: user.user_id,
    public_id: user.public_id,
    email: user.email,
    display_name: user.display_name,
    role: user.role,
    status: 'active',
    created_at: now,
    updated_at: now,
  };
}

function readBearerToken(req: IncomingMessage): string | null {
  const header = req.headers.authorization;
  if (!header?.startsWith('Bearer ')) return null;
  return header.slice('Bearer '.length);
}

function findUserByToken(token: string | null): DevUser | null {
  if (!token?.startsWith(`${AUTH_TOKEN_PREFIX}.`)) return null;
  const userId = token.slice(`${AUTH_TOKEN_PREFIX}.`.length);
  return DEV_USERS.find((user) => user.user_id === userId) ?? null;
}

async function readJsonBody(req: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString('utf8')) as Record<string, unknown>;
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.end(JSON.stringify(body));
}
