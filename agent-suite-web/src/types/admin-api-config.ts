export type AgentName = 'legal' | 'recruitment' | 'data';

export type AgentApiType =
  'deepseek' | 'embedding' | 'vector_db' | 'reranker' | 'ocr' | 'mcp' | 'feishu';

export interface AgentApiConfigView {
  user_public_id: string;
  api_type: string;
  display_name: string;
  base_url: string | null;
  model: string | null;
  api_key_hint: string | null;
  timeout_seconds: number | null;
  max_retries: number | null;
  enabled: boolean;
  extra: Record<string, unknown> | null;
  updated_by: string;
  updated_at: string;
}

export interface AgentApiConfigListEnvelope {
  data: {
    items: AgentApiConfigView[];
  };
  error: null;
}

export interface AgentApiConfigEnvelope {
  data: AgentApiConfigView;
  error: null;
}

export interface AgentApiConfigUpdate {
  display_name: string;
  base_url: string | null;
  model: string | null;
  api_key: string | null;
  timeout_seconds: number | null;
  max_retries: number | null;
  enabled: boolean;
  extra: Record<string, unknown> | null;
}
