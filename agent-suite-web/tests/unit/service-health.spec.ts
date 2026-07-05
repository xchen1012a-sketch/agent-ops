import { describe, expect, it } from 'vitest';

import {
  buildWebConfigHealthItems,
  createCheckingSnapshot,
  probeServiceHealth,
} from '@lib/service-health';
import type { HealthProbeClient, ServiceHealthTarget } from '@/types/health';

const target: ServiceHealthTarget = {
  id: 'legal',
  label: '法律咨询 Agent',
  modulePrefix: '/api/legal/v1',
  livePath: '/health/live',
};

describe('createCheckingSnapshot', () => {
  it('creates a pending snapshot for a service target', () => {
    expect(createCheckingSnapshot(target)).toEqual({
      ...target,
      status: 'checking',
      checkedAt: null,
      detail: '等待检查',
    });
  });
});

describe('probeServiceHealth', () => {
  const fixedNow = () => new Date('2026-07-05T08:00:00.000Z');

  it('maps 2xx responses to healthy', async () => {
    const client: HealthProbeClient = {
      get: async () => ({ status: 200, data: { status: 'ok' } }),
    };

    await expect(probeServiceHealth(target, client, fixedNow)).resolves.toMatchObject({
      status: 'healthy',
      checkedAt: '2026-07-05T08:00:00.000Z',
      detail: '{"status":"ok"}',
    });
  });

  it('maps non-2xx non-5xx responses to degraded', async () => {
    const client: HealthProbeClient = {
      get: async () => ({ status: 404, data: { error_code: 'NOT_FOUND' } }),
    };

    await expect(probeServiceHealth(target, client, fixedNow)).resolves.toMatchObject({
      status: 'degraded',
      detail: '{"error_code":"NOT_FOUND"}',
    });
  });

  it('maps request failures to down with error detail', async () => {
    const client: HealthProbeClient = {
      get: async () => {
        throw { error_code: 'NETWORK_ERROR', message: 'connect ECONNREFUSED' };
      },
    };

    await expect(probeServiceHealth(target, client, fixedNow)).resolves.toMatchObject({
      status: 'down',
      detail: 'NETWORK_ERROR: connect ECONNREFUSED',
    });
  });
});

describe('buildWebConfigHealthItems', () => {
  it('marks required prefixes as ok when configured', () => {
    const items = buildWebConfigHealthItems({
      apiBaseUrl: 'http://localhost',
      authPrefix: '/api/auth',
      legalPrefix: '/api/legal/v1',
      recruitmentPrefix: '/api/recruitment/v1',
      dataPrefix: '/api/data/v1',
      sessionTimeoutMinutes: 30,
    });

    expect(items.every((item) => item.status === 'ok')).toBe(true);
  });

  it('warns for missing base URL and invalid timeout', () => {
    const items = buildWebConfigHealthItems({
      apiBaseUrl: '',
      authPrefix: '/api/auth',
      legalPrefix: '/api/legal/v1',
      recruitmentPrefix: '/api/recruitment/v1',
      dataPrefix: '/api/data/v1',
      sessionTimeoutMinutes: 0,
    });

    expect(items.find((item) => item.key === 'VITE_API_BASE_URL')?.status).toBe('warning');
    expect(items.find((item) => item.key === 'VITE_SESS_TIMEOUT_MINUTES')?.status).toBe(
      'warning',
    );
  });
});
