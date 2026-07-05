import axios from 'axios';

import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';
import { router } from '@router/index';
import type { ApiError } from '@/types/api';

import { createHttpClient, generateRequestId } from './http-client';

interface SuiteEnv {
  apiBaseUrl: string;
  authPrefix: string;
  legalPrefix: string;
  recruitmentPrefix: string;
  dataPrefix: string;
  sessionTimeoutMinutes: number;
}

function readEnv(): SuiteEnv {
  const env = import.meta.env;
  return {
    apiBaseUrl: env.VITE_API_BASE_URL ?? '',
    authPrefix: env.VITE_API_AUTH_PREFIX ?? '/api/auth',
    legalPrefix: env.VITE_API_LEGAL_PREFIX ?? '/api/legal/v1',
    recruitmentPrefix: env.VITE_API_RECRUITMENT_PREFIX ?? '/api/recruitment/v1',
    dataPrefix: env.VITE_API_DATA_PREFIX ?? '/api/data/v1',
    sessionTimeoutMinutes: Number(env.VITE_SESS_TIMEOUT_MINUTES ?? 30),
  };
}

export const suiteEnv = readEnv();

export const legalApi = createHttpClient({
  baseURL: `${suiteEnv.apiBaseUrl}${suiteEnv.legalPrefix}`,
  getAccessToken: () => useAuthStore().accessToken,
  onUnauthorized: () => handleUnauthorized(),
  onForbidden: () => handleForbidden(),
  onRateLimited: (error) => handleRateLimited(error),
  onServerError: (error) => handleServerError(error),
});

export const recruitmentApi = createHttpClient({
  baseURL: `${suiteEnv.apiBaseUrl}${suiteEnv.recruitmentPrefix}`,
  getAccessToken: () => useAuthStore().accessToken,
  onUnauthorized: () => handleUnauthorized(),
  onForbidden: () => handleForbidden(),
  onRateLimited: (error) => handleRateLimited(error),
  onServerError: (error) => handleServerError(error),
});

export const dataApi = createHttpClient({
  baseURL: `${suiteEnv.apiBaseUrl}${suiteEnv.dataPrefix}`,
  getAccessToken: () => useAuthStore().accessToken,
  onUnauthorized: () => handleUnauthorized(),
  onForbidden: () => handleForbidden(),
  onRateLimited: (error) => handleRateLimited(error),
  onServerError: (error) => handleServerError(error),
});

export const authApi = axios.create({
  baseURL: `${suiteEnv.apiBaseUrl}${suiteEnv.authPrefix}`,
  timeout: 15_000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

authApi.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  config.headers['X-Request-ID'] = generateRequestId();
  const token = useAuthStore().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let unauthorizedHandling = false;

async function handleUnauthorized(): Promise<void> {
  if (unauthorizedHandling) return;
  unauthorizedHandling = true;
  const auth = useAuthStore();
  if (auth.accessToken) {
    try {
      await auth.refresh();
      unauthorizedHandling = false;
      return;
    } catch {
      // fall through to clear session
    }
  }
  auth.clearSession();
  useToastStore().warning('登录状态已失效，请重新登录');
  await router.push({
    name: 'login',
    query: { redirect: router.currentRoute.value.fullPath },
  });
  unauthorizedHandling = false;
}

function handleForbidden(): void {
  const current = router.currentRoute.value;
  if (current.name !== 'forbidden') {
    void router.push({ name: 'forbidden' });
  }
}

function handleRateLimited(error: ApiError): void {
  const retryAfter = error.retry_after_seconds;
  const message = retryAfter
    ? `操作过于频繁，请在 ${retryAfter} 秒后重试`
    : '操作过于频繁，请稍后重试';
  useToastStore().warning(message, '限流提示');
}

function handleServerError(error: ApiError): void {
  useToastStore().error(error.message || '服务暂时不可用，请稍后再试', '服务异常');
}

export type { ApiError };
