import type { AgentStreamEvent, StreamState } from '@/types/sse';

/**
 * Suite SSE client.
 * Source of truth: WEB-410 §7 SSE 客户端策略.
 *
 * Uses fetch + ReadableStream so we can send Authorization headers and POST
 * bodies (the native EventSource API is GET-only and does not allow headers).
 *
 * Responsibilities:
 *   - De-dupe events by sequence number.
 *   - Reconnect with exponential backoff (max 3 attempts) using Last-Event-ID.
 *   - Heartbeat watchdog: if no event arrives within HEARTBEAT_TIMEOUT_MS,
 *     treat the stream as broken and reconnect.
 *   - Cancellation: caller-owned AbortController, safe to discard.
 */

export type SseClientHeaders = Record<string, string>;

export interface SseClientOptions {
  url: string;
  token: string | null;
  method?: 'GET' | 'POST';
  body?: BodyInit | null;
  headers?: SseClientHeaders;
  onEvent: (event: AgentStreamEvent) => void;
  onStateChange?: (state: StreamState) => void;
  heartbeatTimeoutMs?: number;
  maxReconnectAttempts?: number;
}

const DEFAULT_HEARTBEAT_TIMEOUT_MS = 30_000;
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 3;
const BACKOFF_BASE_MS = 1_000;
const BACKOFF_MAX_MS = 8_000;

export class AgentStreamClient {
  private readonly options: Required<SseClientOptions>;
  private abortController: AbortController | null = null;
  private lastSequence = 0;
  private lastEventId: string | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setTimeout> | null = null;
  private state: StreamState = 'idle';

  constructor(options: SseClientOptions) {
    this.options = {
      url: options.url,
      token: options.token,
      method: options.method ?? 'GET',
      body: options.body ?? null,
      headers: options.headers ?? {},
      onEvent: options.onEvent,
      onStateChange: options.onStateChange ?? (() => {}),
      heartbeatTimeoutMs: options.heartbeatTimeoutMs ?? DEFAULT_HEARTBEAT_TIMEOUT_MS,
      maxReconnectAttempts: options.maxReconnectAttempts ?? DEFAULT_MAX_RECONNECT_ATTEMPTS,
    };
  }

  start(): void {
    this.resetTimers();
    this.connect();
  }

  stop(): void {
    this.setState('closed');
    this.resetTimers();
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  get currentState(): StreamState {
    return this.state;
  }

  private async connect(): Promise<void> {
    this.abortController = new AbortController();
    this.setState(this.reconnectAttempts === 0 ? 'connecting' : 'reconnecting');

    try {
      const response = await fetch(this.options.url, {
        method: this.options.method,
        headers: this.buildHeaders(),
        body: this.options.body,
        signal: this.abortController.signal,
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status >= 500) {
          throw new Error(`SSE connection failed: HTTP ${response.status}`);
        }
        await this.handleHttpError(response);
        return;
      }
      if (!response.body) {
        throw new Error(`SSE connection failed: HTTP ${response.status}`);
      }

      this.setState('open');
      this.scheduleHeartbeat();

      await this.readStream(response.body);
    } catch (error) {
      this.handleConnectionError(error);
    }
  }

  private async readStream(body: ReadableStream<Uint8Array>): Promise<void> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split('\n\n');
        buffer = frames.pop() ?? '';

        for (const frame of frames) {
          this.processFrame(frame.trim());
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  private processFrame(frame: string): void {
    if (!frame) return;

    this.scheduleHeartbeat();

    const lines = frame.split('\n');
    let dataStr = '';
    let eventName: string | undefined;

    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataStr += line.slice(5).trim();
      } else if (line.startsWith('id:')) {
        this.lastEventId = line.slice(3).trim();
      }
    }

    if (!dataStr) return;

    try {
      const payload = JSON.parse(dataStr) as Record<string, unknown>;
      this.dispatchEvent(this.normalizeEvent(payload, eventName));
    } catch (error) {
      console.warn('[sse] failed to parse event frame', { frame, error });
    }
  }

  private normalizeEvent(payload: Record<string, unknown>, eventName?: string): AgentStreamEvent {
    if (typeof payload.event_id === 'string' && typeof payload.sequence === 'number') {
      return {
        ...(payload as unknown as AgentStreamEvent),
        event: eventName ?? (payload as { event?: string }).event,
      };
    }

    return {
      event_id: this.lastEventId ?? `${eventName ?? 'message'}-${this.lastSequence + 1}`,
      event: eventName,
      run_id: typeof payload.run_id === 'string' ? payload.run_id : '',
      sequence: this.lastSequence + 1,
      timestamp: new Date().toISOString(),
      payload,
    };
  }

  private dispatchEvent(event: AgentStreamEvent): void {
    if (event.sequence && event.sequence <= this.lastSequence) {
      return;
    }
    if (event.sequence) {
      this.lastSequence = event.sequence;
    }
    this.options.onEvent(event);
  }

  private async handleHttpError(response: Response): Promise<void> {
    const message = await readErrorMessage(response);
    this.dispatchEvent({
      event_id: `http-error-${this.lastSequence + 1}`,
      event: 'run.failed',
      run_id: '',
      sequence: this.lastSequence + 1,
      timestamp: new Date().toISOString(),
      payload: {
        error_code: `HTTP_${response.status}`,
        message,
        retryable: response.status >= 500,
      },
    });
    this.setState('error');
  }

  private buildHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      ...this.options.headers,
      Accept: 'text/event-stream',
    };
    if (this.options.token) {
      headers.Authorization = `Bearer ${this.options.token}`;
    }
    if (this.lastEventId) {
      headers['Last-Event-ID'] = this.lastEventId;
    }
    return headers;
  }

  private scheduleHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
    }
    this.heartbeatTimer = setTimeout(() => {
      console.warn('[sse] heartbeat timeout, forcing reconnect');
      this.reconnect();
    }, this.options.heartbeatTimeoutMs);
  }

  private handleConnectionError(error: unknown): void {
    if (this.state === 'closed') return;
    if (error instanceof Error && error.name === 'AbortError') return;

    console.warn('[sse] connection error', error);
    this.reconnect();
  }

  private reconnect(): void {
    this.resetTimers();
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }

    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.setState('error');
      return;
    }

    this.reconnectAttempts += 1;
    const backoffMs = Math.min(BACKOFF_BASE_MS * 2 ** (this.reconnectAttempts - 1), BACKOFF_MAX_MS);
    this.setState('reconnecting');
    this.reconnectTimer = setTimeout(() => {
      void this.connect();
    }, backoffMs);
  }

  private resetTimers(): void {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private setState(next: StreamState): void {
    if (this.state === next) return;
    this.state = next;
    this.options.onStateChange(next);
  }
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as {
      error?: { message?: unknown; code?: unknown };
      detail?: unknown;
    };
    if (typeof payload.error?.message === 'string' && payload.error.message) {
      return payload.error.message;
    }
    if (typeof payload.detail === 'string' && payload.detail) {
      return payload.detail;
    }
    if (typeof payload.error?.code === 'string' && payload.error.code) {
      return payload.error.code;
    }
  } catch {
    // Fall through to the generic HTTP message.
  }
  return `SSE connection failed: HTTP ${response.status}`;
}
