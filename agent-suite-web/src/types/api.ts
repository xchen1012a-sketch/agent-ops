/**
 * Shared API envelope types.
 * These align with the suite's OpenAPI/SSE contract documented in
 * agent-suite-ops/docs/standards/.
 */

export interface ApiEnvelope<T> {
  data: T | null;
  error: ApiError | null;
  meta: ApiMeta | null;
}

export interface ApiError {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
  retry_after_seconds?: number;
  trace_id?: string;
}

export interface ApiMeta {
  request_id?: string;
  pagination?: PaginationMeta;
}

export interface PaginationMeta {
  page: number;
  size: number;
  total: number;
  total_pages: number;
}

export interface PageQuery {
  page?: number;
  size?: number;
}

export interface DateRangeQuery {
  from?: string;
  to?: string;
}

export type HttpStatusCode =
  200 | 201 | 202 | 204 | 400 | 401 | 403 | 404 | 409 | 413 | 422 | 429 | 500 | 503 | 504;

export const API_ERROR_CODES = {
  AUTH_REQUIRED: 'AUTH_REQUIRED',
  AUTH_EXPIRED: 'AUTH_EXPIRED',
  AUTH_FORBIDDEN: 'AUTH_FORBIDDEN',
  RATE_LIMITED: 'RATE_LIMITED',
  AGENT_DEPENDENCY_TIMEOUT: 'AGENT_DEPENDENCY_TIMEOUT',
  LLM_TIMEOUT: 'LLM_TIMEOUT',
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  FILE_TYPE_UNSUPPORTED: 'FILE_TYPE_UNSUPPORTED',
  FILE_SCAN_FAILED: 'FILE_SCAN_FAILED',
  PARSE_FAILED: 'PARSE_FAILED',
  SQL_POLICY_VIOLATION: 'SQL_POLICY_VIOLATION',
  MCP_UNAVAILABLE: 'MCP_UNAVAILABLE',
  INPUT_BLOCKED: 'INPUT_BLOCKED',
  CLASSIFY_FAILED: 'CLASSIFY_FAILED',
  RETRIEVAL_FAILED: 'RETRIEVAL_FAILED',
  CITATION_INVALID: 'CITATION_INVALID',
  DB_UNAVAILABLE: 'DB_UNAVAILABLE',
} as const;

export type ApiErrorCode = (typeof API_ERROR_CODES)[keyof typeof API_ERROR_CODES];
