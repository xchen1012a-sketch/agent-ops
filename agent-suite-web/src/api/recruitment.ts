import { recruitmentApi, suiteEnv } from '@lib/config';
import { AgentStreamClient } from '@lib/sse-client';
import { useAuthStore } from '@stores/auth';
import type {
  RecruitReportCreateEnvelope,
  RecruitReportDetailEnvelope,
  RecruitReportFormat,
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
};
