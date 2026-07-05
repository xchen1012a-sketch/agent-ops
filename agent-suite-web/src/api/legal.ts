import { legalApi } from '@lib/config';
import type {
  LegalConsultationRecordListEnvelope,
  LegalFeedbackEnvelope,
  LegalFeedbackInput,
  LegalHighRiskReviewEnvelope,
  LegalHighRiskReviewInput,
  LegalHighRiskReviewListEnvelope,
  LegalHighRiskReviewResolveEnvelope,
  LegalHighRiskReviewResolveInput,
  LegalMessageListEnvelope,
  LegalQuestionAnswerEnvelope,
  LegalQuestionInput,
  LegalReportEnvelope,
  LegalSessionCreateEnvelope,
  LegalSessionCreateInput,
} from '@/types/legal';

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

  async listHighRiskReviews(
    query: { status?: string; limit?: number; offset?: number } = {},
  ): Promise<LegalHighRiskReviewListEnvelope> {
    const { data } = await legalApi.get<LegalHighRiskReviewListEnvelope>('/high-risk-reviews', {
      params: query,
    });
    return data;
  },

  async resolveHighRiskReview(
    reviewId: number,
    payload: LegalHighRiskReviewResolveInput,
  ): Promise<LegalHighRiskReviewResolveEnvelope> {
    const { data } = await legalApi.post<LegalHighRiskReviewResolveEnvelope>(
      `/high-risk-reviews/${reviewId}/resolution`,
      payload,
    );
    return data;
  },
};
