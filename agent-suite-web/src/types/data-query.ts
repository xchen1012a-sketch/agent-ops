export type DataRunStatus = 'pending' | 'running' | 'success' | 'failed' | 'retrying' | 'canceled';

export type DataThreadStatus = 'active' | 'archived' | string;

export interface DataHealthLive {
  status: string;
}

export interface DataHealthReady {
  status: string;
  db_ok: boolean;
  engine_ready: boolean;
  error: string | null;
}

export interface DataThread {
  thread_id: string;
  title: string | null;
  status: DataThreadStatus;
  created_at: string;
  updated_at: string;
}

export interface DataThreadCreateInput {
  title?: string | null;
}

export interface DataThreadListData {
  items: DataThread[];
  limit: number;
  offset: number;
}

export interface DataRunCreateInput {
  question: string;
  timezone?: string | null;
  locale?: string | null;
  channel?: 'web' | 'feishu';
  idempotency_key?: string | null;
}

export interface DataRun {
  run_id: string;
  thread_id: string;
  status: DataRunStatus | string;
  question: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface DataRunDetail {
  run_id: string;
  status: DataRunStatus | string;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface DataLocalDemoChart {
  type: 'line' | 'bar' | string;
  dataset: Record<string, unknown[]>;
  encoding: Record<string, string>;
}

export interface DataLocalDemoQueryResult {
  columns: string[];
  rows: unknown[][];
}

export interface DataLocalDemoResult {
  question: string;
  source_status: string;
  source_note: string;
  fixture_case_id: string | null;
  generated_sql: string | null;
  policy_allowed: boolean;
  policy_error_code: string | null;
  query_result: DataLocalDemoQueryResult | null;
  answer: string;
  chart: DataLocalDemoChart | null;
  followups: string[];
  node_trace: Array<{ node_name: string; status: string }>;
}

export interface DataQueryHistoryItem {
  query_id: string;
  status: DataRunStatus | string;
  error_code: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface DataQueryHistoryListData {
  items: DataQueryHistoryItem[];
  limit: number;
  offset: number;
}

export interface DataFeishuEventInput {
  type: string;
  challenge?: string | null;
  header?: Record<string, unknown> | null;
  event?: Record<string, unknown> | null;
}

export interface DataFeishuEventResponse {
  event_type: 'challenge' | 'message';
  event_id: string | null;
  duplicate: boolean;
  challenge: string | null;
}

export interface DataEnvelope<T> {
  data: T;
  error: null;
}

export type DataThreadEnvelope = DataEnvelope<DataThread>;
export type DataThreadListEnvelope = DataEnvelope<DataThreadListData>;
export type DataRunEnvelope = DataEnvelope<DataRun>;
export type DataRunDetailEnvelope = DataEnvelope<DataRunDetail>;
export type DataLocalDemoEnvelope = DataEnvelope<DataLocalDemoResult>;
export type DataQueryHistoryListEnvelope = DataEnvelope<DataQueryHistoryListData>;
export type DataQueryHistoryDetailEnvelope = DataEnvelope<DataQueryHistoryItem>;
export type DataFeishuEventEnvelope = DataEnvelope<DataFeishuEventResponse>;

export interface DataSseContractEvent {
  event:
    | 'run.started'
    | 'node.started'
    | 'node.completed'
    | 'node.failed'
    | 'run.completed'
    | 'run.failed'
    | string;
  payload: Record<string, unknown>;
  received_at: string;
}
