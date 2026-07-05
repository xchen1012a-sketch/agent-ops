import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AgentStreamClient } from '@lib/sse-client';
import type { AgentStreamEvent, StreamState } from '@/types/sse';

function createEvent(sequence: number, eventId = `event-${sequence}`): AgentStreamEvent {
  return {
    event_id: eventId,
    run_id: 'run-1',
    sequence,
    timestamp: '2026-07-05T08:00:00.000Z',
    payload: { delta: `chunk-${sequence}` },
  };
}

function encodeFrames(events: AgentStreamEvent[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const frames = events
    .map((event) => `id: ${event.event_id}\ndata: ${JSON.stringify(event)}\n\n`)
    .join('');
  return new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(frames));
      controller.close();
    },
  });
}

describe('AgentStreamClient', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    globalThis.fetch = originalFetch;
  });

  it('dispatches events and skips duplicate or stale sequences', async () => {
    const events: AgentStreamEvent[] = [];
    const states: StreamState[] = [];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: encodeFrames([createEvent(1), createEvent(1, 'duplicate'), createEvent(2)]),
    });
    globalThis.fetch = fetchMock;

    const client = new AgentStreamClient({
      url: '/stream',
      token: 'token-1',
      heartbeatTimeoutMs: 10_000,
      onEvent: (event) => events.push(event),
      onStateChange: (state) => states.push(state),
    });

    client.start();
    await vi.advanceTimersByTimeAsync(0);
    client.stop();

    expect(fetchMock).toHaveBeenCalledWith(
      '/stream',
      expect.objectContaining({
        method: 'GET',
        credentials: 'include',
        headers: expect.objectContaining({ Authorization: 'Bearer token-1' }),
      }),
    );
    expect(events.map((event) => event.sequence)).toEqual([1, 2]);
    expect(states).toContain('connecting');
    expect(states).toContain('open');
  });

  it('aborts the active request when stopped', async () => {
    let signal: AbortSignal | null = null;
    const fetchMock = vi.fn((_url: string, init?: RequestInit) => {
      signal = init?.signal ?? null;
      return new Promise(() => undefined);
    });
    globalThis.fetch = fetchMock as typeof fetch;

    const client = new AgentStreamClient({
      url: '/stream',
      token: null,
      onEvent: () => undefined,
    });

    client.start();
    await vi.advanceTimersByTimeAsync(0);
    client.stop();

    expect(signal?.aborted).toBe(true);
    expect(client.currentState).toBe('closed');
  });

  it('moves to error after reconnect attempts are exhausted', async () => {
    const states: StreamState[] = [];
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 503, body: null });

    const client = new AgentStreamClient({
      url: '/stream',
      token: null,
      heartbeatTimeoutMs: 10_000,
      maxReconnectAttempts: 1,
      onEvent: () => undefined,
      onStateChange: (state) => states.push(state),
    });

    client.start();
    await vi.runAllTimersAsync();

    expect(states).toContain('connecting');
    expect(states).toContain('reconnecting');
    expect(states.at(-1)).toBe('error');
    expect(client.currentState).toBe('error');
  });
});
