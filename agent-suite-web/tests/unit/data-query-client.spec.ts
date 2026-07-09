import { beforeEach, describe, expect, it, vi } from 'vitest';

import { dataQueryClient } from '@api/data-query';
import { dataApi, suiteEnv } from '@lib/config';
import { useAuthStore } from '@stores/auth';

vi.mock('@lib/config', () => ({
  dataApi: {
    post: vi.fn(),
    get: vi.fn(),
  },
  suiteEnv: {
    apiBaseUrl: '',
    dataPrefix: '/api/data/v1',
  },
}));

vi.mock('@stores/auth', () => ({
  useAuthStore: vi.fn(),
}));

const mockedDataApi = vi.mocked(dataApi);
const mockedUseAuthStore = vi.mocked(useAuthStore);

describe('dataQueryClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseAuthStore.mockReturnValue({
      accessToken: 'token-1',
      profile: { public_id: 'user-1' },
    } as ReturnType<typeof useAuthStore>);
    suiteEnv.apiBaseUrl = '';
    suiteEnv.dataPrefix = '/api/data/v1';
  });

  it('maps health endpoints', async () => {
    mockedDataApi.get.mockResolvedValueOnce({ data: { status: 'ok' } });
    mockedDataApi.get.mockResolvedValueOnce({
      data: { status: 'ok', db_ok: true, engine_ready: true, error: null },
    });

    await dataQueryClient.getHealthLive();
    await dataQueryClient.getHealthReady();

    expect(mockedDataApi.get).toHaveBeenCalledWith('/health/live');
    expect(mockedDataApi.get).toHaveBeenCalledWith('/health/ready');
  });

  it('creates and lists threads through public endpoints', async () => {
    mockedDataApi.post.mockResolvedValueOnce({
      data: {
        data: {
          thread_id: 'thread-1',
          title: 'sales',
          status: 'active',
          created_at: '2026-07-05T00:00:00Z',
          updated_at: '2026-07-05T00:00:00Z',
        },
        error: null,
      },
    });
    mockedDataApi.get.mockResolvedValueOnce({
      data: { data: { items: [], limit: 20, offset: 0 }, error: null },
    });

    await dataQueryClient.createThread({ title: 'sales' });
    await dataQueryClient.listThreads({ limit: 20, offset: 0 });

    expect(mockedDataApi.post).toHaveBeenCalledWith('/threads', { title: 'sales' });
    expect(mockedDataApi.get).toHaveBeenCalledWith('/threads', {
      params: { limit: 20, offset: 0 },
    });
  });

  it('encodes thread and run identifiers for run operations', async () => {
    mockedDataApi.get.mockResolvedValue({ data: { data: {}, error: null } });
    mockedDataApi.post.mockResolvedValue({ data: { data: {}, error: null } });

    await dataQueryClient.getThread('thread/1');
    await dataQueryClient.createRun('thread/1', { question: '本周销售额？', channel: 'web' });
    await dataQueryClient.getRun('run/1');
    await dataQueryClient.cancelRun('run/1');
    await dataQueryClient.retryRun('run/1');

    expect(mockedDataApi.get).toHaveBeenCalledWith('/threads/thread%2F1');
    expect(mockedDataApi.post).toHaveBeenCalledWith('/threads/thread%2F1/runs', {
      question: '本周销售额？',
      channel: 'web',
    });
    expect(mockedDataApi.get).toHaveBeenCalledWith('/runs/run%2F1');
    expect(mockedDataApi.post).toHaveBeenCalledWith('/runs/run%2F1/cancel');
    expect(mockedDataApi.post).toHaveBeenCalledWith('/runs/run%2F1/retry');
  });

  it('maps query history endpoints', async () => {
    mockedDataApi.get.mockResolvedValue({
      data: { data: { items: [], limit: 20, offset: 0 }, error: null },
    });

    await dataQueryClient.listQueryHistory({ limit: 20, offset: 0 });
    await dataQueryClient.getQueryHistory('query/1');

    expect(mockedDataApi.get).toHaveBeenCalledWith('/query-history', {
      params: { limit: 20, offset: 0 },
    });
    expect(mockedDataApi.get).toHaveBeenCalledWith('/query-history/query%2F1');
  });

  it('maps mock Feishu event endpoint with signature header', async () => {
    mockedDataApi.post.mockResolvedValueOnce({
      data: {
        data: {
          event_type: 'challenge',
          event_id: null,
          duplicate: false,
          challenge: 'challenge-1',
        },
        error: null,
      },
    });

    await dataQueryClient.handleFeishuEvent(
      { type: 'url_verification', challenge: 'challenge-1' },
      'mock-signature',
    );

    expect(mockedDataApi.post).toHaveBeenCalledWith(
      '/integrations/feishu/events',
      { type: 'url_verification', challenge: 'challenge-1' },
      { headers: { 'X-Feishu-Signature': 'mock-signature' } },
    );
  });

  it('creates run stream with data prefix and gateway subject header', () => {
    const stream = dataQueryClient.createRunStream({
      runId: 'run/1',
      onEvent: () => undefined,
    });

    expect(stream.currentState).toBe('idle');
  });
});
