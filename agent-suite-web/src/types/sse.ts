import type { Citation, LegalHighRiskFlag } from './agent';

export type AgentStreamEventName =
  | 'run.started'
  | 'node.started'
  | 'node.completed'
  | 'message.delta'
  | 'message.completed'
  | 'run.completed'
  | 'run.failed'
  | 'run.canceled'
  | 'heartbeat';

export interface AgentStreamEvent<T = unknown> {
  event_id: string;
  event?: AgentStreamEventName | string;
  request_id?: string;
  run_id: string;
  thread_id?: string;
  sequence: number;
  timestamp: string;
  payload: T;
}

export interface NodeStartedPayload {
  node_name: string;
  metadata?: Record<string, unknown>;
}

export interface MessageDeltaPayload {
  delta: string;
  cumulative_length?: number;
}

export interface MessageCompletedPayload {
  content: string;
  citations?: Citation[];
  high_risk?: LegalHighRiskFlag;
}

export interface RunCompletedPayload {
  citations?: Citation[];
  high_risk?: LegalHighRiskFlag;
  message_id?: string;
}

export interface RunFailedPayload {
  error_code: string;
  message: string;
  retryable: boolean;
}

export type StreamState = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed' | 'error';
