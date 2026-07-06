export type LegalSessionStatus = 'active' | 'archived' | 'deleted';
export type LegalMessageRole = 'user' | 'assistant' | 'system';

export interface LegalSession {
  public_id: string;
  title: string | null;
  status: LegalSessionStatus;
  last_message_at: string | null;
}

export interface LegalSessionCreateInput {
  category_code: string;
  title?: string | null;
}

export interface LegalSessionCreateEnvelope {
  data: LegalSession;
  error: null;
}

export interface LegalSessionEnvelope {
  data: LegalSession;
  error: null;
}

export interface LegalSessionListData {
  items: LegalSession[];
  limit: number;
  offset: number;
}

export interface LegalSessionListEnvelope {
  data: LegalSessionListData;
  error: null;
}

export interface LegalCitation {
  source?: string;
  section?: string;
  snippet?: string;
  [key: string]: unknown;
}

export interface LegalMessage {
  public_id: string;
  role: LegalMessageRole;
  content: string;
  citations: LegalCitation[] | null;
  high_risk: boolean;
  prompt_version: string | null;
}

export interface LegalMessageListData {
  items: LegalMessage[];
  limit: number;
  offset: number;
}

export interface LegalMessageListEnvelope {
  data: LegalMessageListData;
  error: null;
}

export interface LegalQuestionInput {
  question: string;
}

export interface LegalMessageRef {
  public_id: string;
}

export interface LegalQuestionAnswer {
  question_message: LegalMessageRef;
  answer_message: LegalMessageRef;
  answer: string;
  citations: LegalCitation[];
  high_risk: boolean;
  risk_reason: string | null;
  category: string | null;
  node_trace: string[];
}

export interface LegalQuestionAnswerEnvelope {
  data: LegalQuestionAnswer;
  error: null;
}

export interface LegalConsultationRecord {
  public_id: string;
  summary: string;
  citations: LegalCitation[] | null;
  high_risk: boolean;
  disclaimer: string;
}

export interface LegalConsultationRecordListData {
  items: LegalConsultationRecord[];
  limit: number;
  offset: number;
  query: string | null;
}

export interface LegalConsultationRecordListEnvelope {
  data: LegalConsultationRecordListData;
  error: null;
}

export interface LegalReport {
  record_public_id: string;
  format: 'markdown';
  content: string;
}

export interface LegalReportEnvelope {
  data: LegalReport;
  error: null;
}

export interface LegalFeedbackInput {
  rating: number;
  comment?: string | null;
}

export interface LegalFeedback {
  id: number | null;
  rating: number;
  comment: string | null;
}

export interface LegalFeedbackEnvelope {
  data: LegalFeedback;
  error: null;
}

export type LegalHighRiskReviewStatus = 'pending' | 'reviewed' | 'resolved';

export interface LegalHighRiskReviewInput {
  reason: string;
}

export interface LegalHighRiskReview {
  id: number | null;
  reason: string;
  status: LegalHighRiskReviewStatus;
}

export interface LegalHighRiskReviewEnvelope {
  data: LegalHighRiskReview;
  error: null;
}
