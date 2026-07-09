import { computed, getCurrentScope, onScopeDispose, ref, type ComputedRef, type Ref } from 'vue';

import type { AgentStreamClient } from '@lib/sse-client';
import type { AgentStreamEvent, StreamState } from '@/types/sse';

/**
 * Agent thinking/answer stream state machine (STREAM-100).
 *
 * Wraps an AgentStreamClient factory and drives the phase transitions
 * idle → thinking → answering → done (or error). Splits the SSE event stream
 * into a thinking buffer and an answer buffer and tracks the "已思考 X 秒"
 * duration. Business and model agnostic: it only understands the shared SSE
 * event contract, so it is copyable across the three agent frontends.
 */
export type StreamPhase = 'idle' | 'thinking' | 'answering' | 'done' | 'error';

export interface AgentStreamClientHandlers {
  onEvent: (event: AgentStreamEvent) => void;
  onStateChange: (state: StreamState) => void;
}

export interface UseAgentStreamOptions {
  /** Build a client bound to the given handlers. Called on each start(). */
  createClient: (handlers: AgentStreamClientHandlers) => AgentStreamClient;
  /** Timer resolution for the live thinking counter. Default 250ms. */
  tickMs?: number;
}

export interface QueryResultSummary {
  sql: string | null;
  columns: string[];
  sampleRows: unknown[][];
  rowCount: number;
  truncated: boolean;
  errorCode: string | null;
}

export interface UseAgentStreamReturn {
  phase: Ref<StreamPhase>;
  thinkingText: Ref<string>;
  answerText: Ref<string>;
  thinkingElapsedSeconds: Ref<number>;
  thinkingDurationMs: Ref<number | null>;
  panelExpanded: Ref<boolean>;
  streamState: Ref<StreamState>;
  errorMessage: Ref<string | null>;
  queryResult: Ref<QueryResultSummary | null>;
  isStreaming: ComputedRef<boolean>;
  start: () => void;
  stop: () => void;
  reset: () => void;
  togglePanel: () => void;
}

export function useAgentStream(options: UseAgentStreamOptions): UseAgentStreamReturn {
  const tickMs = Math.max(50, options.tickMs ?? 250);

  const phase = ref<StreamPhase>('idle');
  const thinkingText = ref('');
  const answerText = ref('');
  const thinkingElapsedSeconds = ref(0);
  const thinkingDurationMs = ref<number | null>(null);
  const panelExpanded = ref(false);
  const streamState = ref<StreamState>('idle');
  const errorMessage = ref<string | null>(null);
  const queryResult = ref<QueryResultSummary | null>(null);

  const isStreaming = computed(() => phase.value === 'thinking' || phase.value === 'answering');

  let client: AgentStreamClient | null = null;
  let thinkingStartedAt: number | null = null;
  let thinkingTimer: ReturnType<typeof setInterval> | null = null;

  function startThinkingTimer(): void {
    stopThinkingTimer();
    thinkingStartedAt = Date.now();
    thinkingElapsedSeconds.value = 0;
    thinkingTimer = setInterval(() => {
      if (thinkingStartedAt === null) return;
      thinkingElapsedSeconds.value = Math.max(1, Math.round((Date.now() - thinkingStartedAt) / 1000));
    }, tickMs);
  }

  function stopThinkingTimer(): void {
    if (thinkingTimer !== null) {
      clearInterval(thinkingTimer);
      thinkingTimer = null;
    }
  }

  function freezeThinking(serverDurationMs?: number): void {
    if (typeof serverDurationMs === 'number' && serverDurationMs >= 0) {
      thinkingDurationMs.value = serverDurationMs;
    } else if (thinkingStartedAt !== null) {
      thinkingDurationMs.value = Date.now() - thinkingStartedAt;
    }
    if (thinkingDurationMs.value !== null) {
      thinkingElapsedSeconds.value = Math.max(1, Math.round(thinkingDurationMs.value / 1000));
    }
    stopThinkingTimer();
  }

  function enterAnswering(serverDurationMs?: number): void {
    if (phase.value === 'thinking') {
      freezeThinking(serverDurationMs);
      panelExpanded.value = false;
    }
    phase.value = 'answering';
  }

  function handleEvent(event: AgentStreamEvent): void {
    const payload = (event.payload ?? {}) as Record<string, unknown>;
    switch (event.event) {
      case 'message.thinking.delta': {
        if (phase.value === 'idle') {
          phase.value = 'thinking';
          panelExpanded.value = true;
          startThinkingTimer();
        }
        if (typeof payload.delta === 'string') {
          thinkingText.value += payload.delta;
        }
        break;
      }
      case 'message.thinking.completed': {
        const durationMs = typeof payload.duration_ms === 'number' ? payload.duration_ms : undefined;
        enterAnswering(durationMs);
        break;
      }
      case 'message.delta': {
        if (phase.value !== 'answering') {
          enterAnswering();
        }
        if (typeof payload.delta === 'string') {
          answerText.value += payload.delta;
        }
        break;
      }
      case 'message.completed':
      case 'run.completed': {
        if (phase.value === 'thinking') {
          freezeThinking();
          panelExpanded.value = false;
        }
        queryResult.value = extractQueryResult(payload);
        phase.value = 'done';
        stop();
        break;
      }
      case 'run.failed': {
        errorMessage.value =
          typeof payload.message === 'string' ? payload.message : '流式生成失败';
        phase.value = 'error';
        stopThinkingTimer();
        stop();
        break;
      }
      default:
        break;
    }
  }

  function handleStateChange(state: StreamState): void {
    streamState.value = state;
    if (state === 'error' && phase.value !== 'done') {
      errorMessage.value = errorMessage.value ?? '流式连接中断';
      phase.value = 'error';
      stopThinkingTimer();
    }
  }

  function reset(): void {
    stopThinkingTimer();
    client?.stop();
    client = null;
    thinkingStartedAt = null;
    phase.value = 'idle';
    thinkingText.value = '';
    answerText.value = '';
    thinkingElapsedSeconds.value = 0;
    thinkingDurationMs.value = null;
    panelExpanded.value = false;
    streamState.value = 'idle';
    errorMessage.value = null;
    queryResult.value = null;
  }

  function start(): void {
    reset();
    client = options.createClient({ onEvent: handleEvent, onStateChange: handleStateChange });
    client.start();
  }

  function stop(): void {
    stopThinkingTimer();
    client?.stop();
    client = null;
  }

  function togglePanel(): void {
    panelExpanded.value = !panelExpanded.value;
  }

  if (getCurrentScope()) {
    onScopeDispose(stop);
  }

  return {
    phase,
    thinkingText,
    answerText,
    thinkingElapsedSeconds,
    thinkingDurationMs,
    panelExpanded,
    streamState,
    errorMessage,
    queryResult,
    isStreaming,
    start,
    stop,
    reset,
    togglePanel,
  };
}

function extractQueryResult(payload: Record<string, unknown>): QueryResultSummary | null {
  const hasSqlOrColumns = payload.sql !== undefined || Array.isArray(payload.columns);
  if (!hasSqlOrColumns) return null;
  const columns = Array.isArray(payload.columns) ? (payload.columns as string[]) : [];
  const rawRows = Array.isArray(payload.sample_rows) ? (payload.sample_rows as unknown[][]) : [];
  return {
    sql: typeof payload.sql === 'string' ? payload.sql : null,
    columns,
    sampleRows: rawRows,
    rowCount: typeof payload.row_count === 'number' ? payload.row_count : rawRows.length,
    truncated: Boolean(payload.truncated),
    errorCode: typeof payload.error_code === 'string' ? payload.error_code : null,
  };
}
