import type { PageQuery } from './api';

export interface AgentThread {
  thread_id: string;
  category?: string;
  title?: string;
  created_at: string;
  updated_at?: string;
  last_message_at?: string;
}

export interface AgentRun {
  run_id: string;
  thread_id: string;
  status: AgentRunStatus;
  created_at?: string;
  finished_at?: string;
}

export type AgentRunStatus = 'pending' | 'running' | 'success' | 'failed' | 'retrying' | 'canceled';

export interface Citation {
  source: string;
  section?: string;
  snippet: string;
}

export interface LegalHighRiskFlag {
  high_risk: boolean;
  reason?: string;
  escalation_channel?: string;
}

export interface LegalSessionListQuery extends PageQuery {
  keyword?: string;
  from?: string;
  to?: string;
}

export interface RecruitmentMatchResult {
  tier: 'high' | 'medium' | 'low';
  evidence: RecruitmentEvidence[];
  gaps: string[];
  interview_questions: string[];
}

export interface RecruitmentEvidence {
  topic: string;
  detail: string;
  weight?: number;
}

export interface DataQueryResult {
  summary: string;
  table?: DataTableResult;
  chart?: DataChartSpec;
  followups: string[];
  sql_visible: boolean;
}

export interface DataTableResult {
  columns: string[];
  rows: unknown[][];
}

export interface DataChartSpec {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'area';
  title?: string;
  echarts_option: unknown;
}

export interface DataSqlAuditRow {
  audit_id: string;
  user_id: string;
  started_at: string;
  duration_ms: number;
  row_count: number;
  status: 'success' | 'blocked' | 'failed';
  sql_preview?: string;
}
