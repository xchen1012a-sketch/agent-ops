import { dataApi, suiteEnv } from '@lib/config';
import { AgentStreamClient, type SseClientHeaders } from '@lib/sse-client';
import { useAuthStore } from '@stores/auth';
import type { AgentStreamEvent, StreamState } from '@/types/sse';
import type {
  DataFeishuEventEnvelope,
  DataFeishuEventInput,
  DataHealthLive,
  DataHealthReady,
  DataLocalDemoEnvelope,
  DataQueryHistoryDetailEnvelope,
  DataQueryHistoryListEnvelope,
  DataRunCreateInput,
  DataRunDetailEnvelope,
  DataRunEnvelope,
  DataThreadCreateInput,
  DataThreadEnvelope,
  DataThreadListEnvelope,
} from '@/types/data-query';

interface PageQuery {
  limit?: number;
  offset?: number;
}

export interface DataRunStreamOptions {
  runId: string;
  onEvent: (event: AgentStreamEvent) => void;
  onStateChange?: (state: StreamState) => void;
}

export interface DataRunCompletionStreamOptions {
  threadId: string;
  question: string;
  onEvent: (event: AgentStreamEvent) => void;
  onStateChange?: (state: StreamState) => void;
}

export const dataQueryClient = {
  async getHealthLive(): Promise<DataHealthLive> {
    const { data } = await dataApi.get<DataHealthLive>('/health/live');
    return data;
  },

  async getHealthReady(): Promise<DataHealthReady> {
    const { data } = await dataApi.get<DataHealthReady>('/health/ready');
    return data;
  },

  async createThread(payload: DataThreadCreateInput): Promise<DataThreadEnvelope> {
    const { data } = await dataApi.post<DataThreadEnvelope>('/threads', payload);
    return data;
  },

  async listThreads(query: PageQuery = {}): Promise<DataThreadListEnvelope> {
    const { data } = await dataApi.get<DataThreadListEnvelope>('/threads', { params: query });
    return data;
  },

  async getThread(threadId: string): Promise<DataThreadEnvelope> {
    const { data } = await dataApi.get<DataThreadEnvelope>(
      `/threads/${encodeURIComponent(threadId)}`,
    );
    return data;
  },

  async createRun(threadId: string, payload: DataRunCreateInput): Promise<DataRunEnvelope> {
    const { data } = await dataApi.post<DataRunEnvelope>(
      `/threads/${encodeURIComponent(threadId)}/runs`,
      payload,
    );
    return data;
  },

  async createLocalDemoRun(
    threadId: string,
    payload: DataRunCreateInput,
  ): Promise<DataLocalDemoEnvelope> {
    const { data } = await dataApi.post<DataLocalDemoEnvelope>(
      `/threads/${encodeURIComponent(threadId)}/runs/local-demo`,
      payload,
    );
    return data;
  },

  async getRun(runId: string): Promise<DataRunDetailEnvelope> {
    const { data } = await dataApi.get<DataRunDetailEnvelope>(`/runs/${encodeURIComponent(runId)}`);
    return data;
  },

  async cancelRun(runId: string): Promise<DataRunDetailEnvelope> {
    const { data } = await dataApi.post<DataRunDetailEnvelope>(
      `/runs/${encodeURIComponent(runId)}/cancel`,
    );
    return data;
  },

  async retryRun(runId: string): Promise<DataRunDetailEnvelope> {
    const { data } = await dataApi.post<DataRunDetailEnvelope>(
      `/runs/${encodeURIComponent(runId)}/retry`,
    );
    return data;
  },

  async listQueryHistory(query: PageQuery = {}): Promise<DataQueryHistoryListEnvelope> {
    const { data } = await dataApi.get<DataQueryHistoryListEnvelope>('/query-history', {
      params: query,
    });
    return data;
  },

  async getQueryHistory(queryId: string): Promise<DataQueryHistoryDetailEnvelope> {
    const { data } = await dataApi.get<DataQueryHistoryDetailEnvelope>(
      `/query-history/${encodeURIComponent(queryId)}`,
    );
    return data;
  },

  async handleFeishuEvent(
    payload: DataFeishuEventInput,
    signature: string,
  ): Promise<DataFeishuEventEnvelope> {
    const { data } = await dataApi.post<DataFeishuEventEnvelope>(
      '/integrations/feishu/events',
      payload,
      { headers: { 'X-Feishu-Signature': signature } },
    );
    return data;
  },

  createRunStream(options: DataRunStreamOptions): AgentStreamClient {
    return new AgentStreamClient({
      url: buildDataApiUrl(`/runs/${encodeURIComponent(options.runId)}/stream`),
      token: useAuthStore().accessToken,
      headers: buildDataStreamHeaders(),
      onEvent: options.onEvent,
      onStateChange: options.onStateChange,
    });
  },

  createRunCompletionStream(options: DataRunCompletionStreamOptions): AgentStreamClient {
    return new AgentStreamClient({
      url: buildDataApiUrl(`/threads/${encodeURIComponent(options.threadId)}/runs/stream`),
      method: 'POST',
      body: JSON.stringify({ question: options.question }),
      token: useAuthStore().accessToken,
      headers: { ...buildDataStreamHeaders(), 'Content-Type': 'application/json' },
      onEvent: options.onEvent,
      onStateChange: options.onStateChange,
    });
  },
};

function buildDataApiUrl(path: string): string {
  return `${suiteEnv.apiBaseUrl}${suiteEnv.dataPrefix}${path}`;
}

function buildDataStreamHeaders(): SseClientHeaders {
  const subject = useAuthStore().profile?.public_id;
  return subject ? { 'X-User-Subject': subject } : {};
}
