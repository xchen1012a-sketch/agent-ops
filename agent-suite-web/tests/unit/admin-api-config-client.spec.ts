import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  buildDefaultAgentApiConfigs,
  listAgentApiConfigs,
} from '@api/admin-api-config';
import { legalApi } from '@lib/config';

vi.mock('@lib/config', () => ({
  legalApi: {
    get: vi.fn(),
    put: vi.fn(),
  },
  recruitmentApi: {
    get: vi.fn(),
    put: vi.fn(),
  },
  dataApi: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

const mockedLegalApi = vi.mocked(legalApi);

describe('admin API config client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('builds default editable rows for legal dependencies', () => {
    const rows = buildDefaultAgentApiConfigs('legal', 'user-1');

    expect(rows.map((row) => row.api_type)).toEqual([
      'deepseek',
      'embedding',
      'vector_db',
      'reranker',
      'ocr',
    ]);
    expect(rows[0]).toMatchObject({
      user_public_id: 'user-1',
      enabled: false,
      api_key_hint: null,
    });
  });

  it('merges backend rows with default dependency rows and suppresses global load errors', async () => {
    mockedLegalApi.get.mockResolvedValueOnce({
      data: {
        data: {
          items: [
            {
              user_public_id: 'user-1',
              api_type: 'deepseek',
              display_name: 'Custom DeepSeek',
              base_url: 'https://api.example.invalid',
              model: 'deepseek-chat',
              api_key_hint: 'sk-***-1234',
              timeout_seconds: 60,
              max_retries: 2,
              enabled: true,
              extra: null,
              updated_by: 'user-1',
              updated_at: '2026-07-05T00:00:00.000Z',
            },
          ],
        },
        error: null,
      },
    });

    const rows = await listAgentApiConfigs('legal');

    expect(mockedLegalApi.get).toHaveBeenCalledWith('/me/api-config', {
      suppressGlobalError: true,
    });
    expect(rows.map((row) => row.api_type)).toEqual([
      'deepseek',
      'embedding',
      'vector_db',
      'reranker',
      'ocr',
    ]);
    expect(rows[0].display_name).toBe('Custom DeepSeek');
    expect(rows[1].api_key_hint).toBeNull();
  });
});
