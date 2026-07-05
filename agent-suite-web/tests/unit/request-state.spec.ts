import { describe, expect, it } from 'vitest';

import { API_ERROR_CODES } from '@/types/api';
import {
  createCancelledState,
  createIdleState,
  createLoadingState,
  createSuccessState,
  isDataEmpty,
  mapRequestError,
} from '@lib/request-state';

const fixedClock = {
  now: () => new Date('2026-07-05T08:00:00.000Z'),
};

describe('request state factory', () => {
  it('creates idle and loading states', () => {
    expect(createIdleState()).toEqual({
      status: 'idle',
      data: null,
      error: null,
      updatedAt: null,
    });

    expect(createLoadingState(fixedClock)).toEqual({
      status: 'loading',
      data: null,
      error: null,
      updatedAt: '2026-07-05T08:00:00.000Z',
    });
  });

  it('maps successful empty arrays to empty status', () => {
    const state = createSuccessState([], { clock: fixedClock });

    expect(state.status).toBe('empty');
    expect(state.data).toEqual([]);
    expect(state.updatedAt).toBe('2026-07-05T08:00:00.000Z');
  });

  it('maps successful data to success status', () => {
    const state = createSuccessState({ id: 'record-1' }, { clock: fixedClock });

    expect(state.status).toBe('success');
    expect(state.data).toEqual({ id: 'record-1' });
  });

  it('allows custom empty detection', () => {
    const state = createSuccessState(
      { total: 0 },
      { clock: fixedClock, isEmpty: (value) => value.total === 0 },
    );

    expect(state.status).toBe('empty');
  });

  it('creates cancelled state with non-retryable error view', () => {
    const state = createCancelledState();

    expect(state.status).toBe('cancelled');
    expect(state.error).toMatchObject({
      code: 'REQUEST_CANCELLED',
      title: '已取消',
      retryable: false,
    });
  });
});

describe('isDataEmpty', () => {
  it('detects null, blank strings, arrays and page-like items', () => {
    expect(isDataEmpty(null)).toBe(true);
    expect(isDataEmpty('  ')).toBe(true);
    expect(isDataEmpty([])).toBe(true);
    expect(isDataEmpty({ items: [] })).toBe(true);
    expect(isDataEmpty({ items: [1] })).toBe(false);
    expect(isDataEmpty({ value: 0 })).toBe(false);
  });
});

describe('mapRequestError', () => {
  it('maps auth errors to non-retryable views', () => {
    expect(mapRequestError({ error_code: API_ERROR_CODES.AUTH_EXPIRED })).toMatchObject({
      code: API_ERROR_CODES.AUTH_EXPIRED,
      title: '登录已过期',
      retryable: false,
      actionLabel: '重新登录',
    });

    expect(mapRequestError({ error_code: API_ERROR_CODES.AUTH_FORBIDDEN })).toMatchObject({
      code: API_ERROR_CODES.AUTH_FORBIDDEN,
      title: '暂不能访问',
      retryable: false,
    });
  });

  it('maps rate limit with retry-after detail', () => {
    expect(
      mapRequestError({
        error_code: API_ERROR_CODES.RATE_LIMITED,
        message: 'too many requests',
        retry_after_seconds: 10,
      }),
    ).toMatchObject({
      code: API_ERROR_CODES.RATE_LIMITED,
      message: 'too many requests',
      retryable: true,
      retryAfterSeconds: 10,
    });
  });

  it('maps service and network errors as retryable', () => {
    expect(mapRequestError({ error_code: API_ERROR_CODES.AGENT_DEPENDENCY_TIMEOUT })).toMatchObject(
      {
        title: '暂时不可用',
        retryable: true,
      },
    );

    expect(mapRequestError({ error_code: 'NETWORK_ERROR' })).toMatchObject({
      title: '网络异常',
      retryable: true,
    });
  });

  it('preserves unknown error messages and trace ids', () => {
    expect(
      mapRequestError({
        error_code: 'CUSTOM_ERROR',
        message: 'custom failure',
        trace_id: 'trace-1',
      }),
    ).toMatchObject({
      code: 'CUSTOM_ERROR',
      message: 'custom failure',
      traceId: 'trace-1',
      retryable: true,
    });
  });
});
