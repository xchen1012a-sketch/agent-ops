import { API_ERROR_CODES } from '@/types/api';
import type {
  RequestErrorInput,
  RequestErrorSource,
  RequestErrorView,
  RequestState,
  RequestStateClock,
  RequestStateOptions,
} from '@/types/request-state';

const DEFAULT_CLOCK: RequestStateClock = {
  now: () => new Date(),
};

const ERROR_VIEW_BY_CODE: Record<
  string,
  Omit<RequestErrorView, 'code' | 'retryAfterSeconds' | 'traceId'>
> = {
  [API_ERROR_CODES.AUTH_REQUIRED]: {
    title: '先登录',
    message: '登录后就能继续。',
    tone: 'warning',
    retryable: false,
    actionLabel: '登录',
  },
  [API_ERROR_CODES.AUTH_EXPIRED]: {
    title: '登录已过期',
    message: '请重新登录后继续。',
    tone: 'warning',
    retryable: false,
    actionLabel: '重新登录',
  },
  [API_ERROR_CODES.AUTH_FORBIDDEN]: {
    title: '暂不能访问',
    message: '当前账号还不能使用这个功能。',
    tone: 'warning',
    retryable: false,
    actionLabel: '知道了',
  },
  [API_ERROR_CODES.RATE_LIMITED]: {
    title: '慢一点',
    message: '操作太快了，稍后再试。',
    tone: 'warning',
    retryable: true,
    actionLabel: '稍后重试',
  },
  [API_ERROR_CODES.AGENT_DEPENDENCY_TIMEOUT]: {
    title: '暂时不可用',
    message: '服务正在恢复，稍后再试。',
    tone: 'danger',
    retryable: true,
    actionLabel: '重试',
  },
  [API_ERROR_CODES.LLM_TIMEOUT]: {
    title: '还没想好',
    message: '这次等待太久了，请再试一次。',
    tone: 'warning',
    retryable: true,
    actionLabel: '重试',
  },
  NETWORK_ERROR: {
    title: '网络异常',
    message: '连接失败，请稍后重试。',
    tone: 'danger',
    retryable: true,
    actionLabel: '重试',
  },
  REQUEST_CANCELLED: {
    title: '已取消',
    message: '操作已取消。',
    tone: 'info',
    retryable: false,
    actionLabel: '知道了',
  },
};

export function createIdleState<T>(): RequestState<T> {
  return {
    status: 'idle',
    data: null,
    error: null,
    updatedAt: null,
  };
}

export function createLoadingState<T>(clock: RequestStateClock = DEFAULT_CLOCK): RequestState<T> {
  return {
    status: 'loading',
    data: null,
    error: null,
    updatedAt: toIsoString(clock),
  };
}

export function createSuccessState<T>(
  data: T,
  options: RequestStateOptions<T> = {},
): RequestState<T> {
  const clock = options.clock ?? DEFAULT_CLOCK;
  const empty = options.isEmpty?.(data) ?? isDataEmpty(data);
  return {
    status: empty ? 'empty' : 'success',
    data,
    error: null,
    updatedAt: toIsoString(clock),
  };
}

export function createEmptyState<T>(data: T | null = null): RequestState<T> {
  return {
    status: 'empty',
    data,
    error: null,
    updatedAt: toIsoString(DEFAULT_CLOCK),
  };
}

export function createErrorState<T>(error: RequestErrorInput): RequestState<T> {
  return {
    status: 'error',
    data: null,
    error: mapRequestError(error),
    updatedAt: toIsoString(DEFAULT_CLOCK),
  };
}

export function createCancelledState<T>(): RequestState<T> {
  return {
    status: 'cancelled',
    data: null,
    error: mapRequestError({ error_code: 'REQUEST_CANCELLED' }),
    updatedAt: toIsoString(DEFAULT_CLOCK),
  };
}

/**
 * Normalize a caught `unknown` into a mappable request error WITHOUT
 * stringifying objects. The suite throws plain `ApiError` objects
 * (`{ error_code, message }`), so `String(error)` would collapse them to
 * "[object Object]"; keeping the object lets `mapRequestError` surface the
 * real backend message and error code instead.
 */
export function toRequestError(error: unknown): RequestErrorInput {
  if (error instanceof Error) return error;
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object') return error as RequestErrorSource;
  return null;
}

export function mapRequestError(error: RequestErrorInput): RequestErrorView {
  const source = normalizeErrorSource(error);
  const code = source.error_code ?? 'UNKNOWN_ERROR';
  const view = ERROR_VIEW_BY_CODE[code] ?? {
    title: code.startsWith('AUTH_') ? '认证异常' : '请求失败',
    message: '请求失败，请稍后重试。',
    tone: 'danger' as const,
    retryable: true,
    actionLabel: '重试',
  };

  return {
    code,
    title: view.title,
    message: source.message || view.message,
    tone: view.tone,
    retryable: view.retryable,
    actionLabel: view.actionLabel,
    retryAfterSeconds: source.retry_after_seconds,
    traceId: source.trace_id,
  };
}

export function isDataEmpty(data: unknown): boolean {
  if (data == null) return true;
  if (Array.isArray(data)) return data.length === 0;
  if (typeof data === 'string') return data.trim().length === 0;
  if (typeof data === 'object' && 'items' in data) {
    const items = (data as { items?: unknown }).items;
    return Array.isArray(items) && items.length === 0;
  }
  return false;
}

function normalizeErrorSource(error: RequestErrorInput): RequestErrorSource {
  if (!error) {
    return { error_code: 'UNKNOWN_ERROR' };
  }
  if (typeof error === 'string') {
    return { error_code: 'UNKNOWN_ERROR', message: error };
  }
  if (error instanceof Error) {
    return { error_code: 'UNKNOWN_ERROR', message: error.message };
  }
  return error;
}

function toIsoString(clock: RequestStateClock): string {
  return clock.now().toISOString();
}
