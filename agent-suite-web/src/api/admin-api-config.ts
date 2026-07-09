import type { AxiosInstance } from 'axios';

import { dataApi, legalApi, recruitmentApi } from '@lib/config';
import type { SuiteAxiosRequestConfig } from '@lib/http-client';
import type {
  AgentApiConfigEnvelope,
  AgentApiConfigListEnvelope,
  AgentApiConfigUpdate,
  AgentApiConfigView,
  AgentName,
} from '@/types/admin-api-config';

const clientsByAgent: Record<AgentName, AxiosInstance> = {
  legal: legalApi,
  recruitment: recruitmentApi,
  data: dataApi,
};

const defaultApiTypesByAgent: Record<AgentName, { api_type: string; display_name: string }[]> = {
  legal: [
    { api_type: 'deepseek', display_name: 'DeepSeek LLM（必需）' },
    { api_type: 'embedding', display_name: 'Embedding 服务（法律 RAG）' },
    { api_type: 'vector_db', display_name: '向量库（法律 RAG）' },
    { api_type: 'reranker', display_name: 'Reranker（法律 RAG）' },
    { api_type: 'ocr', display_name: 'OCR（扫描材料可选）' },
  ],
  recruitment: [
    { api_type: 'deepseek', display_name: 'DeepSeek LLM（必需）' },
    { api_type: 'ocr', display_name: 'OCR（扫描简历/JD 可选）' },
  ],
  data: [
    { api_type: 'deepseek', display_name: 'DeepSeek LLM（必需）' },
    { api_type: 'mcp', display_name: 'MCP 查询服务（真查询）' },
    { api_type: 'feishu', display_name: '飞书（消息入口可选）' },
  ],
};

export function buildDefaultAgentApiConfigs(
  agent: AgentName,
  userPublicId = '',
): AgentApiConfigView[] {
  return defaultApiTypesByAgent[agent].map((item) => ({
    user_public_id: userPublicId,
    api_type: item.api_type,
    display_name: item.display_name,
    base_url: null,
    model: null,
    api_key_hint: null,
    timeout_seconds: null,
    max_retries: null,
    enabled: false,
    extra: null,
    updated_by: userPublicId,
    updated_at: new Date(0).toISOString(),
  }));
}

export async function listAgentApiConfigs(agent: AgentName): Promise<AgentApiConfigView[]> {
  const client = clientsByAgent[agent];
  const requestConfig: SuiteAxiosRequestConfig = { suppressGlobalError: true };
  const response = await client.get<AgentApiConfigListEnvelope>('/me/api-config', requestConfig);
  const items = response.data.data.items;
  const userPublicId = items[0]?.user_public_id ?? '';
  const merged = new Map(
    buildDefaultAgentApiConfigs(agent, userPublicId).map((item) => [item.api_type, item]),
  );
  for (const item of items) {
    merged.set(item.api_type, item);
  }
  return Array.from(merged.values());
}

export async function updateAgentApiConfig(
  agent: AgentName,
  apiType: string,
  payload: AgentApiConfigUpdate,
): Promise<AgentApiConfigView> {
  const client = clientsByAgent[agent];
  const response = await client.put<AgentApiConfigEnvelope>(`/me/api-config/${apiType}`, payload);
  return response.data.data;
}
