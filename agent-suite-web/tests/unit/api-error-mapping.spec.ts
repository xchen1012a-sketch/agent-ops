import { AxiosError, AxiosHeaders } from 'axios';
import { describe, expect, it } from 'vitest';

import { API_ERROR_CODES } from '@/types/api';
import { generateRequestId } from '@lib/http-client';

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
