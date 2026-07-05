import { legalApi, suiteEnv } from '@lib/config';
import { AgentStreamClient, type SseClientHeaders } from '@lib/sse-client';
import { useAuthStore } from '@stores/auth';
import type { AgentStreamEvent, StreamState } from '@/types/sse';
import type {
  LegalConsultationRecordListEnvelope,
  LegalFeedbackEnvelope,
  LegalFeedbackInput,
  LegalHighRiskReviewEnvelope,
  LegalHighRiskReviewInput,
  LegalMessageListEnvelope,
  LegalQuestionAnswerEnvelope,
  LegalQuestionInput,
  LegalReportEnvelope,
  LegalSessionCreateEnvelope,
  LegalSessionCreateInput,
} from '@/types/legal';

export interface LegalQuestionStreamOptions {
  sessionPublicId: string;
  question: string;
  onEvent: (event: AgentStreamEvent) => void;
  onStateChange?: (state: StreamState) => void;
}

export const legalClient = {
  async createSession(payload: LegalSessionCreateInput): Promise<LegalSessionCreateEnvelope> {
    const { data } = await legalApi.post<LegalSessionCreateEnvelope>('/sessions', payload);
    return data;
  },

  async listMessages(
    sessionPublicId: string,
    query: { limit?: number; offset?: number } = {},
  ): Promise<LegalMessageListEnvelope> {
    const { data } = await legalApi.get<LegalMessageListEnvelope>(
      `/sessions/${encodeURIComponent(sessionPublicId)}/messages`,
      { params: query },
    );
    return data;
  },

  async answerQuestion(
    sessionPublicId: string,
    payload: LegalQuestionInput,
  ): Promise<LegalQuestionAnswerEnvelope> {
    const { data } = await legalApi.post<LegalQuestionAnswerEnvelope>(
      `/sessions/${encodeURIComponent(sessionPublicId)}/questions`,
      payload,
    );
    return data;
  },

  createQuestionStream(options: LegalQuestionStreamOptions): AgentStreamClient {
    return new AgentStreamClient({
      url: buildLegalApiUrl(
        `/sessions/${encodeURIComponent(options.sessionPublicId)}/questions/events`,
      ),
      method: 'POST',
      body: JSON.stringify({ question: options.question }),
      token: useAuthStore().accessToken,
      headers: buildLegalStreamHeaders(),
      onEvent: options.onEvent,
      onStateChange: options.onStateChange,
    });
  },

  async listConsultationRecords(
    query: { limit?: number; offset?: number; q?: string } = {},
  ): Promise<LegalConsultationRecordListEnvelope> {
    const { data } = await legalApi.get<LegalConsultationRecordListEnvelope>(
      '/consultation-records',
      { params: query },
    );
    return data;
  },

  async getConsultationReport(recordPublicId: string): Promise<LegalReportEnvelope> {
    const { data } = await legalApi.get<LegalReportEnvelope>(
      `/consultation-records/${encodeURIComponent(recordPublicId)}/report`,
    );
    return data;
  },

  async createFeedback(
    sessionPublicId: string,
    messagePublicId: string,
    payload: LegalFeedbackInput,
  ): Promise<LegalFeedbackEnvelope> {
    const { data } = await legalApi.post<LegalFeedbackEnvelope>(
      `/sessions/${encodeURIComponent(sessionPublicId)}/messages/${encodeURIComponent(messagePublicId)}/feedback`,
      payload,
    );
    return data;
  },

  async createHighRiskReview(
    sessionPublicId: string,
    messagePublicId: string,
    payload: LegalHighRiskReviewInput,
  ): Promise<LegalHighRiskReviewEnvelope> {
    const { data } = await legalApi.post<LegalHighRiskReviewEnvelope>(
      `/sessions/${encodeURIComponent(sessionPublicId)}/messages/${encodeURIComponent(
        messagePublicId,
      )}/high-risk-review`,
      payload,
    );
    return data;
  },
};

function buildLegalApiUrl(path: string): string {
  return `${suiteEnv.apiBaseUrl}${suiteEnv.legalPrefix}${path}`;
}

function buildLegalStreamHeaders(): SseClientHeaders {
  const auth = useAuthStore();
  const headers: SseClientHeaders = {
    'Content-Type': 'application/json',
  };
  if (auth.profile?.public_id) {
    headers['X-User-Public-Id'] = auth.profile.public_id;
  }
  if (auth.role) {
    headers['X-User-Role'] = auth.role;
  }
  return headers;
}
