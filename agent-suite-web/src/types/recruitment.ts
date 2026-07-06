import type { AgentStreamEvent, StreamState } from './sse';

// 鏉ユ簮锛歳ecruitment-assistant-agent domain/value_objects/recruit_enums.py
export type RecruitTaskStatus =
  'uploaded' | 'parsing' | 'parsed' | 'matching' | 'reviewing' | 'completed' | 'failed';

export type RecruitTaskPriority = 'normal' | 'urgent';

export type RecruitReviewStatus = 'pending' | 'approved' | 'rejected' | 'changes_requested';

export type RecruitScanStatus = 'pending' | 'clean' | 'infected' | 'failed';

export type RecruitRunStatus =
  'pending' | 'running' | 'success' | 'failed' | 'retrying' | 'canceled';

// ---- 浠诲姟涓庢潗鏂欙紙schemas/recruitment_tasks.py锛?---

export interface RecruitMaterialSummary {
  has_resume: boolean;
  has_jd: boolean;
  resume_material_id: string | null;
  jd_material_id: string | null;
}

export interface RecruitMaterial {
  material_id: string;
  kind: string;
  scan_status: RecruitScanStatus;
  original_deleted: boolean;
  size_chars: number;
}

export interface RecruitTask {
  task_id: string;
  title: string | null;
  priority: RecruitTaskPriority;
  status: RecruitTaskStatus;
  review_status: RecruitReviewStatus;
  material_summary: RecruitMaterialSummary;
  latest_run_id: string | null;
  created_at: string;
}

export interface RecruitTaskDetail extends RecruitTask {
  materials: RecruitMaterial[];
}

export interface RecruitTaskCreateInput {
  title?: string | null;
  priority?: RecruitTaskPriority;
  resume_text?: string | null;
  jd_text?: string | null;
}

export interface RecruitTaskCreateResponse {
  request_id: string;
  task: RecruitTask;
}

export interface RecruitTaskListResponse {
  request_id: string;
  items: RecruitTask[];
  page: number;
  page_size: number;
  total: number;
}

export interface RecruitTaskDetailEnvelope {
  request_id: string;
  task: RecruitTaskDetail;
}

export interface RecruitTaskListQuery {
  page?: number;
  page_size?: number;
  status?: RecruitTaskStatus;
  review_status?: RecruitReviewStatus;
}

// ---- 杩愯锛坰chemas/recruitment_runs.py锛?---

export interface RecruitRun {
  run_id: string;
  task_id: string;
  thread_id: string;
  status: RecruitRunStatus;
  error_code: string | null;
  node_trace: string[];
  created_at: string;
  completed_at: string | null;
}

export interface RecruitRunStartInput {
  prompt_version?: string;
  workflow_version?: string;
}

export interface RecruitRunStartResponse {
  request_id: string;
  run: RecruitRun;
  stream_url: string;
}

export interface RecruitRunEnvelope {
  request_id: string;
  run: RecruitRun;
}

// ---- 管理员复核（schemas/recruitment_admin.py）----

export interface RecruitReviewInput {
  review_status: RecruitReviewStatus;
  review_note?: string | null;
}

export interface RecruitReview {
  task_id: string;
  review_status: RecruitReviewStatus;
  review_note: string | null;
  reviewed_by: string;
  reviewed_at: string;
}

export interface RecruitReviewEnvelope {
  request_id: string;
  review: RecruitReview;
}

// ---- 鎶ュ憡锛坰chemas/recruitment_reports.py锛?---

export interface RecruitReportSummary {
  report_id: string;
  task_id: string;
  status: string;
  format_available: string[];
  expires_at: string;
}

export interface RecruitReportDetail extends RecruitReportSummary {
  content_markdown: string;
}

export interface RecruitReportCreateEnvelope {
  request_id: string;
  report: RecruitReportSummary;
}

export interface RecruitReportDetailEnvelope {
  request_id: string;
  report: RecruitReportDetail;
}

export type RecruitReportFormat = 'md' | 'pdf';

// ---- SSE 杩愯娴?----

export interface RecruitRunStreamOptions {
  runId: string;
  onEvent: (event: AgentStreamEvent) => void;
  onStateChange?: (state: StreamState) => void;
}
