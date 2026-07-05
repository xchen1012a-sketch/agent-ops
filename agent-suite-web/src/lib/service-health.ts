import type {
  HealthProbeClient,
  HealthProbeFailure,
  ServiceHealthSnapshot,
  ServiceHealthTarget,
  WebConfigHealthItem,
} from '@/types/health';

export function createCheckingSnapshot(target: ServiceHealthTarget): ServiceHealthSnapshot {
  return {
    ...target,
    status: 'checking',
    checkedAt: null,
    detail: '等待检查',
  };
}

export async function probeServiceHealth(
  target: ServiceHealthTarget,
  client: HealthProbeClient,
  now: () => Date = () => new Date(),
): Promise<ServiceHealthSnapshot> {
  try {
    const response = await client.get(target.livePath, {
      validateStatus: (status) => status < 500,
    });
    return {
      ...target,
      status: response.status >= 200 && response.status < 300 ? 'healthy' : 'degraded',
      checkedAt: now().toISOString(),
      detail: formatHealthDetail(response.data),
    };
  } catch (error) {
    return {
      ...target,
      status: 'down',
      checkedAt: now().toISOString(),
      detail: formatHealthError(error),
    };
  }
}

export function buildWebConfigHealthItems(env: {
  apiBaseUrl: string;
  authPrefix: string;
  legalPrefix: string;
  recruitmentPrefix: string;
  dataPrefix: string;
  sessionTimeoutMinutes: number;
}): WebConfigHealthItem[] {
  return [
    createRequiredConfigItem('VITE_API_BASE_URL', 'API 网关基地址', env.apiBaseUrl),
    createRequiredConfigItem('VITE_API_AUTH_PREFIX', '认证 API 前缀', env.authPrefix),
    createRequiredConfigItem('VITE_API_LEGAL_PREFIX', '法律 Agent API 前缀', env.legalPrefix),
    createRequiredConfigItem(
      'VITE_API_RECRUITMENT_PREFIX',
      '招聘 Agent API 前缀',
      env.recruitmentPrefix,
    ),
    createRequiredConfigItem('VITE_API_DATA_PREFIX', '智能问数 API 前缀', env.dataPrefix),
    {
      key: 'VITE_SESS_TIMEOUT_MINUTES',
      label: '前端会话空闲超时',
      value: String(env.sessionTimeoutMinutes),
      status:
        Number.isFinite(env.sessionTimeoutMinutes) && env.sessionTimeoutMinutes > 0
          ? 'ok'
          : 'warning',
      detail:
        Number.isFinite(env.sessionTimeoutMinutes) && env.sessionTimeoutMinutes > 0
          ? '已配置为正数分钟'
          : '配置缺失或不是正数，可能导致会话空闲检测不可用',
    },
  ];
}

function createRequiredConfigItem(key: string, label: string, value: string): WebConfigHealthItem {
  const normalized = value.trim();
  return {
    key,
    label,
    value: normalized || '未配置',
    status: normalized ? 'ok' : 'warning',
    detail: normalized ? '已配置' : '缺少配置，相关请求可能无法发出',
  };
}

function formatHealthDetail(data: unknown): string {
  if (typeof data === 'string') {
    return data || '服务返回空文本';
  }
  if (data === null || typeof data === 'undefined') {
    return '服务未返回详情';
  }
  try {
    return JSON.stringify(data);
  } catch {
    return '服务详情无法序列化';
  }
}

function formatHealthError(error: unknown): string {
  if (isHealthProbeFailure(error) && error.message) {
    return error.error_code ? `${error.error_code}: ${error.message}` : error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

function isHealthProbeFailure(error: unknown): error is HealthProbeFailure {
  return typeof error === 'object' && error !== null;
}
