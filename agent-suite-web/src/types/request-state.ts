import type { ApiError } from './api';

export type RequestStatus = 'idle' | 'loading' | 'success' | 'empty' | 'error' | 'cancelled';

export type RequestErrorTone = 'info' | 'warning' | 'danger';

export interface RequestErrorView {
  code: string;
  title: string;
  message: string;
  tone: RequestErrorTone;
  retryable: boolean;
  actionLabel: string;
  retryAfterSeconds?: number;
  traceId?: string;
}

export interface RequestState<T> {
  status: RequestStatus;
  data: T | null;
  error: RequestErrorView | null;
  updatedAt: string | null;
}

export interface RequestStateClock {
  now: () => Date;
}

export interface RequestStateOptions<T> {
  isEmpty?: (data: T) => boolean;
  clock?: RequestStateClock;
}

export interface RequestErrorSource {
  error_code?: string;
  message?: string;
  retry_after_seconds?: number;
  trace_id?: string;
}

export type RequestErrorInput = ApiError | RequestErrorSource | Error | string | null | undefined;
