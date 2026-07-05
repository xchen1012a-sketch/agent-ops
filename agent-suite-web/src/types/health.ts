import type { ApiError } from './api';

export type ServiceHealthStatus = 'checking' | 'healthy' | 'degraded' | 'down';

export type ServiceHealthId = 'legal' | 'recruitment' | 'data';

export interface ServiceHealthTarget {
  id: ServiceHealthId;
  label: string;
  modulePrefix: string;
  livePath: string;
}

export interface ServiceHealthSnapshot extends ServiceHealthTarget {
  status: ServiceHealthStatus;
  checkedAt: string | null;
  detail: string;
}

export interface HealthProbeResponse {
  status: number;
  data: unknown;
}

export interface HealthProbeClient {
  get(
    path: string,
    config?: { validateStatus?: (status: number) => boolean },
  ): Promise<HealthProbeResponse>;
}

export interface HealthProbeFailure {
  error_code?: ApiError['error_code'];
  message?: string;
}

export interface WebConfigHealthItem {
  key: string;
  label: string;
  value: string;
  status: 'ok' | 'warning';
  detail: string;
}
