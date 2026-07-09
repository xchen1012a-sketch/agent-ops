import { AxiosError, AxiosHeaders } from 'axios';
import { describe, expect, it, vi } from 'vitest';

import { API_ERROR_CODES } from '@/types/api';
import { createHttpClient, generateRequestId } from '@lib/http-client';

describe('generateRequestId', () => {
  it('returns a non-empty string', () => {
    const id = generateRequestId();
    expect(typeof id).toBe('string');
    expect(id.length).toBeGreaterThan(0);
  });

  it('returns unique values', () => {
    const ids = new Set(Array.from({ length: 10 }, () => generateRequestId()));
    expect(ids.size).toBe(10);
  });
});

describe('API_ERROR_CODES', () => {
  it('contains the suite-level error codes', () => {
    expect(API_ERROR_CODES.AUTH_REQUIRED).toBe('AUTH_REQUIRED');
    expect(API_ERROR_CODES.AUTH_EXPIRED).toBe('AUTH_EXPIRED');
    expect(API_ERROR_CODES.AUTH_FORBIDDEN).toBe('AUTH_FORBIDDEN');
    expect(API_ERROR_CODES.RATE_LIMITED).toBe('RATE_LIMITED');
    expect(API_ERROR_CODES.LLM_TIMEOUT).toBe('LLM_TIMEOUT');
    expect(API_ERROR_CODES.SQL_POLICY_VIOLATION).toBe('SQL_POLICY_VIOLATION');
  });
});

describe('AxiosError shape', () => {
  it('preserves status code on response errors', () => {
    const error = new AxiosError(
      'Forbidden',
      '403',
      { headers: new AxiosHeaders() },
      {},
      {
        status: 403,
        statusText: 'Forbidden',
        headers: {},
        config: { headers: new AxiosHeaders() },
        data: { error_code: 'AUTH_FORBIDDEN', message: 'no access' },
      },
    );
    expect(error.response?.status).toBe(403);
  });
});

describe('createHttpClient data-query subject header', () => {
  it('normalizes nested backend error envelope', async () => {
    const adapter = vi.fn().mockRejectedValue(
      new AxiosError(
        'Forbidden',
        '403',
        { headers: new AxiosHeaders() },
        {},
        {
          status: 403,
          statusText: 'Forbidden',
          headers: {},
          config: { headers: new AxiosHeaders() },
          data: {
            request_id: 'req-1',
            error: {
              code: 'AUTH_FORBIDDEN',
              message: 'access denied',
              retryable: false,
              details: { scope: 'query-history' },
            },
          },
        },
      ),
    );
    const client = createHttpClient({
      baseURL: '/api/data/v1',
      getAccessToken: () => null,
    });

    await expect(client.get('/query-history', { adapter })).rejects.toMatchObject({
      error_code: 'AUTH_FORBIDDEN',
      message: 'access denied',
      details: { scope: 'query-history' },
      trace_id: 'req-1',
    });
  });

  it('adds X-User-Subject when configured', async () => {
    const adapter = vi.fn().mockResolvedValue({
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {},
      data: {},
    });
    const client = createHttpClient({
      baseURL: '/api/data/v1',
      getAccessToken: () => 'token-1',
      getUserSubject: () => 'user-1',
    });

    await client.get('/threads', { adapter });

    const config = adapter.mock.calls[0][0];
    expect(config.headers.Authorization).toBe('Bearer token-1');
    expect(config.headers['X-User-Subject']).toBe('user-1');
  });

  it('adds x-user-public-id when configured', async () => {
    const adapter = vi.fn().mockResolvedValue({
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {},
      data: {},
    });
    const client = createHttpClient({
      baseURL: '/api/recruitment/v1',
      getAccessToken: () => 'token-1',
      getUserPublicId: () => 'user-1',
    });

    await client.get('/me/api-config', { adapter });

    const config = adapter.mock.calls[0][0];
    expect(config.headers.Authorization).toBe('Bearer token-1');
    expect(config.headers['x-user-public-id']).toBe('user-1');
  });
});
