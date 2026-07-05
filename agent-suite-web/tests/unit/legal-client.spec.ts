import { beforeEach, describe, expect, it, vi } from 'vitest';

import { legalClient } from '@api/legal';
import { legalApi } from '@lib/config';

vi.mock('@lib/config', () => ({
  legalApi: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

const mockedLegalApi = vi.mocked(legalApi);

describe('legalClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates a legal session through the public sessions endpoint', async () => {
    mockedLegalApi.post.mockResolvedValueOnce({
      data: {
        data: {
          public_id: 'session-1',
          title: '劳动合同咨询',
          status: 'active',
          last_message_at: null,
        },
        error: null,
      },
    });

    const response = await legalClient.createSession({
      category_code: 'labor',
      title: '劳动合同咨询',
    });

    expect(mockedLegalApi.post).toHaveBeenCalledWith('/sessions', {
      category_code: 'labor',
      title: '劳动合同咨询',
    });
    expect(response.data.public_id).toBe('session-1');
  });

  it('loads messages with encoded session id and pagination params', async () => {
    mockedLegalApi.get.mockResolvedValueOnce({
      data: { data: { items: [], limit: 20, offset: 0 }, error: null },
    });

    await legalClient.listMessages('session/id', { limit: 20, offset: 0 });

    expect(mockedLegalApi.get).toHaveBeenCalledWith('/sessions/session%2Fid/messages', {
      params: { limit: 20, offset: 0 },
    });
  });

  it('submits a deterministic legal question', async () => {
    mockedLegalApi.post.mockResolvedValueOnce({
      data: {
        data: {
          question_message: { public_id: 'q-1' },
          answer_message: { public_id: 'a-1' },
          answer: '请保留劳动合同和工资流水。',
          citations: [],
          high_risk: false,
          risk_reason: null,
          category: 'labor',
          node_trace: ['input_safety'],
        },
        error: null,
      },
    });

    const response = await legalClient.answerQuestion('session-1', {
      question: '公司拖欠工资怎么办？',
    });

    expect(mockedLegalApi.post).toHaveBeenCalledWith('/sessions/session-1/questions', {
      question: '公司拖欠工资怎么办？',
    });
    expect(response.data.answer_message.public_id).toBe('a-1');
  });

  it('loads consultation records with search params', async () => {
    mockedLegalApi.get.mockResolvedValueOnce({
      data: {
        data: { items: [], limit: 20, offset: 0, query: '劳动' },
        error: null,
      },
    });

    await legalClient.listConsultationRecords({ limit: 20, offset: 0, q: '劳动' });

    expect(mockedLegalApi.get).toHaveBeenCalledWith('/consultation-records', {
      params: { limit: 20, offset: 0, q: '劳动' },
    });
  });

  it('loads a markdown consultation report with encoded record id', async () => {
    mockedLegalApi.get.mockResolvedValueOnce({
      data: {
        data: { record_public_id: 'record/1', format: 'markdown', content: '# report' },
        error: null,
      },
    });

    await legalClient.getConsultationReport('record/1');

    expect(mockedLegalApi.get).toHaveBeenCalledWith('/consultation-records/record%2F1/report');
  });

  it('creates feedback for an assistant message', async () => {
    mockedLegalApi.post.mockResolvedValueOnce({
      data: { data: { id: 1, rating: 5, comment: '有帮助' }, error: null },
    });

    await legalClient.createFeedback('session/1', 'message/1', {
      rating: 5,
      comment: '有帮助',
    });

    expect(mockedLegalApi.post).toHaveBeenCalledWith(
      '/sessions/session%2F1/messages/message%2F1/feedback',
      { rating: 5, comment: '有帮助' },
    );
  });

  it('queues a high-risk review for an assistant message', async () => {
    mockedLegalApi.post.mockResolvedValueOnce({
      data: { data: { id: 2, reason: '涉及人身安全', status: 'pending' }, error: null },
    });

    await legalClient.createHighRiskReview('session-1', 'message-1', {
      reason: '涉及人身安全',
    });

    expect(mockedLegalApi.post).toHaveBeenCalledWith(
      '/sessions/session-1/messages/message-1/high-risk-review',
      { reason: '涉及人身安全' },
    );
  });

  it('lists and resolves high-risk reviews', async () => {
    mockedLegalApi.get.mockResolvedValueOnce({
      data: { data: { items: [], limit: 20, offset: 0, status: 'pending' }, error: null },
    });
    mockedLegalApi.post.mockResolvedValueOnce({
      data: {
        data: {
          id: 2,
          message_id: 10,
          user_id: 20,
          reason: '涉及人身安全',
          status: 'resolved',
          reviewed_by: 1,
          resolution: '已电话回访',
        },
        error: null,
      },
    });

    await legalClient.listHighRiskReviews({ status: 'pending', limit: 20, offset: 0 });
    await legalClient.resolveHighRiskReview(2, {
      status: 'resolved',
      resolution: '已电话回访',
    });

    expect(mockedLegalApi.get).toHaveBeenCalledWith('/high-risk-reviews', {
      params: { status: 'pending', limit: 20, offset: 0 },
    });
    expect(mockedLegalApi.post).toHaveBeenCalledWith('/high-risk-reviews/2/resolution', {
      status: 'resolved',
      resolution: '已电话回访',
    });
  });
});
