import { recruitmentApi, suiteEnv } from '@lib/config';
import { AgentStreamClient } from '@lib/sse-client';
import { useAuthStore } from '@stores/auth';
import type { AgentStreamEvent, StreamState } from '@/types/sse';
import type {
  RecruitReportCreateEnvelope,
  RecruitReportDetailEnvelope,
  RecruitReportFormat,
  RecruitReviewEnvelope,
  RecruitReviewInput,
  RecruitRunEnvelope,
  RecruitRunStartInput,
  RecruitRunStartResponse,
  RecruitRunStreamOptions,
  RecruitTaskCreateInput,
  RecruitTaskCreateResponse,
  RecruitTaskDetailEnvelope,
  RecruitTaskListQuery,
  RecruitTaskListResponse,
} from '@/types/recruitment';

export interface RecruitRunCompletionStreamOptions {
  taskId: string;
  onEvent: (event: AgentStreamEvent) => void;
  onStateChange?: (state: StreamState) => void;
}

export const recruitmentClient = {
  async createTask(payload: RecruitTaskCreateInput): Promise<RecruitTaskCreateResponse> {
    const { data } = await recruitmentApi.post<RecruitTaskCreateResponse>(
      '/recruitment-tasks',
      payload,
    );
    return data;
  },

  async listTasks(query: RecruitTaskListQuery = {}): Promise<RecruitTaskListResponse> {
    const { data } = await recruitmentApi.get<RecruitTaskListResponse>('/recruitment-tasks', {
      params: query,
    });
    return data;
  },

  async getTask(taskId: string): Promise<RecruitTaskDetailEnvelope> {
    const { data } = await recruitmentApi.get<RecruitTaskDetailEnvelope>(
      `/recruitment-tasks/${encodeURIComponent(taskId)}`,
    );
    return data;
  },

  async deleteTask(taskId: string): Promise<void> {
    await recruitmentApi.delete(`/recruitment-tasks/${encodeURIComponent(taskId)}`);
  },

  async startRun(
    taskId: string,
    payload: RecruitRunStartInput = {},
  ): Promise<RecruitRunStartResponse> {
    const { data } = await recruitmentApi.post<RecruitRunStartResponse>(
      `/recruitment-tasks/${encodeURIComponent(taskId)}/runs`,
      payload,
    );
    return data;
  },

  async getRun(runId: string): Promise<RecruitRunEnvelope> {
    const { data } = await recruitmentApi.get<RecruitRunEnvelope>(
      `/recruitment-runs/${encodeURIComponent(runId)}`,
    );
    return data;
  },

  async cancelRun(runId: string): Promise<RecruitRunEnvelope> {
    const { data } = await recruitmentApi.post<RecruitRunEnvelope>(
      `/recruitment-runs/${encodeURIComponent(runId)}/cancel`,
    );
    return data;
  },

  async reviewTask(taskId: string, payload: RecruitReviewInput): Promise<RecruitReviewEnvelope> {
    const { data } = await recruitmentApi.post<RecruitReviewEnvelope>(
      `/admin/recruitment-tasks/${encodeURIComponent(taskId)}/review`,
      payload,
    );
    return data;
  },

  async createReport(taskId: string): Promise<RecruitReportCreateEnvelope> {
    const { data } = await recruitmentApi.post<RecruitReportCreateEnvelope>(
      `/recruitment-tasks/${encodeURIComponent(taskId)}/reports`,
    );
    return data;
  },

  async getReport(reportId: string): Promise<RecruitReportDetailEnvelope> {
    const { data } = await recruitmentApi.get<RecruitReportDetailEnvelope>(
      `/recruitment-reports/${encodeURIComponent(reportId)}`,
    );
    return data;
  },

  buildReportExportUrl(reportId: string, format: RecruitReportFormat = 'md'): string {
    return `${suiteEnv.apiBaseUrl}${suiteEnv.recruitmentPrefix}/recruitment-reports/${encodeURIComponent(
      reportId,
    )}/export?format=${format}`;
  },

  createRunStream(options: RecruitRunStreamOptions): AgentStreamClient {
    return new AgentStreamClient({
      url: `${suiteEnv.apiBaseUrl}${suiteEnv.recruitmentPrefix}/recruitment-runs/${encodeURIComponent(
        options.runId,
      )}/stream`,
      token: useAuthStore().accessToken,
      onEvent: options.onEvent,
      onStateChange: options.onStateChange,
    });
  },

  createRunCompletionStream(options: RecruitRunCompletionStreamOptions): AgentStreamClient {
    return new AgentStreamClient({
      url: `${suiteEnv.apiBaseUrl}${suiteEnv.recruitmentPrefix}/recruitment-tasks/${encodeURIComponent(
        options.taskId,
      )}/runs/stream`,
      method: 'POST',
      body: JSON.stringify({}),
      token: useAuthStore().accessToken,
      headers: buildRecruitmentStreamHeaders(),
      onEvent: options.onEvent,
      onStateChange: options.onStateChange,
    });
  },
};

function buildRecruitmentStreamHeaders(): Record<string, string> {
  const auth = useAuthStore();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (auth.profile?.public_id) {
    headers['X-User-Public-Id'] = auth.profile.public_id;
  }
  if (auth.role) {
    headers['X-User-Role'] = auth.role;
  }
  return headers;
}
