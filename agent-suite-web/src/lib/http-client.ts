import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';

import { API_ERROR_CODES, type ApiError } from '@/types/api';

const DEFAULT_TIMEOUT_MS = 30_000;

export interface HttpClientOptions {
  baseURL: string;
  timeoutMs?: number;
  getAccessToken: () => string | null;
  onUnauthorized?: (error: ApiError) => void;
  onForbidden?: (error: ApiError) => void;
  onRateLimited?: (error: ApiError) => void;
  onServerError?: (error: ApiError) => void;
}

export function createHttpClient(options: HttpClientOptions): AxiosInstance {
  const client = axios.create({
    baseURL: options.baseURL,
    timeout: options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    withCredentials: true,
  });

  client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = options.getAccessToken();
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    config.headers = config.headers ?? {};
    config.headers['X-Request-ID'] = generateRequestId();
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiError>) => {
      const apiError = normalizeError(error);
      routeError(apiError, options);
      return Promise.reject(apiError);
    },
  );

  return client;
}

export function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function normalizeError(error: AxiosError<ApiError>): ApiError {
  if (error.response) {
    const { status, data } = error.response;
    if (data && typeof data.error_code === 'string') {
      return data;
    }
    return {
      error_code: mapStatusToErrorCode(status),
      message: data?.message ?? error.message ?? `HTTP ${status}`,
    };
  }
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
    return {
      error_code: API_ERROR_CODES.AGENT_DEPENDENCY_TIMEOUT,
      message: '请求超时，请稍后再试',
    };
  }
  return {
    error_code: 'NETWORK_ERROR',
    message: error.message ?? '网络连接异常',
  };
}

function mapStatusToErrorCode(status: number): string {
  switch (status) {
    case 401:
      return API_ERROR_CODES.AUTH_EXPIRED;
    case 403:
      return API_ERROR_CODES.AUTH_FORBIDDEN;
    case 429:
      return API_ERROR_CODES.RATE_LIMITED;
    case 413:
      return API_ERROR_CODES.FILE_TOO_LARGE;
    case 422:
      return API_ERROR_CODES.PARSE_FAILED;
    case 503:
      return API_ERROR_CODES.AGENT_DEPENDENCY_TIMEOUT;
    case 504:
      return API_ERROR_CODES.LLM_TIMEOUT;
    default:
      return status >= 500 ? API_ERROR_CODES.AGENT_DEPENDENCY_TIMEOUT : 'UNKNOWN_ERROR';
  }
}

function routeError(error: ApiError, options: HttpClientOptions): void {
  switch (error.error_code) {
    case API_ERROR_CODES.AUTH_REQUIRED:
    case API_ERROR_CODES.AUTH_EXPIRED:
      options.onUnauthorized?.(error);
      break;
    case API_ERROR_CODES.AUTH_FORBIDDEN:
      options.onForbidden?.(error);
      break;
    case API_ERROR_CODES.RATE_LIMITED:
      options.onRateLimited?.(error);
      break;
    default:
      if (error.error_code.startsWith('AGENT_') || error.error_code === 'NETWORK_ERROR') {
        options.onServerError?.(error);
      }
  }
}

export type { AxiosRequestConfig };
