import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAgentStream, type AgentStreamClientHandlers } from '@/composables/useAgentStream';
import type { AgentStreamClient } from '@lib/sse-client';
import type { AgentStreamEvent } from '@/types/sse';

function event(name: string, payload: Record<string, unknown> = {}): AgentStreamEvent {
  return {
    event_id: `${name}-1`,
    event: name,
    run_id: 'run-1',
    sequence: 1,
    timestamp: '2026-07-06T00:00:00.000Z',
    payload,
  };
}

function setup() {
  let captured: AgentStreamClientHandlers | null = null;
  const fakeClient = { start: vi.fn(), stop: vi.fn() } as unknown as AgentStreamClient;
  const stream = useAgentStream({
    createClient: (handlers) => {
      captured = handlers;
      return fakeClient;
    },
  });
  stream.start();
  if (captured === null) throw new Error('createClient was not invoked');
  return { stream, emit: (captured as AgentStreamClientHandlers).onEvent, fakeClient };
}

describe('useAgentStream', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('drives idle → thinking → answering → done and splits the two channels', () => {
    const { stream, emit, fakeClient } = setup();
    expect(stream.phase.value).toBe('idle');

    emit(event('message.thinking.delta', { delta: '想' }));
    emit(event('message.thinking.delta', { delta: '一下' }));
    expect(stream.phase.value).toBe('thinking');
    expect(stream.panelExpanded.value).toBe(true);
    expect(stream.thinkingText.value).toBe('想一下');

    emit(event('message.thinking.completed', { duration_ms: 1500 }));
    expect(stream.phase.value).toBe('answering');
    expect(stream.panelExpanded.value).toBe(false);
    expect(stream.thinkingDurationMs.value).toBe(1500);

    emit(event('message.delta', { delta: '答案' }));
    emit(event('message.delta', { delta: '继续' }));
    expect(stream.answerText.value).toBe('答案继续');
    expect(stream.phase.value).toBe('answering');

    emit(event('message.completed', { content: '答案继续' }));
    expect(stream.phase.value).toBe('done');
    expect(fakeClient.stop).toHaveBeenCalled();
  });

  it('auto-collapses when answer starts without an explicit thinking.completed', () => {
    const { stream, emit } = setup();
    emit(event('message.thinking.delta', { delta: '思考' }));
    expect(stream.panelExpanded.value).toBe(true);

    emit(event('message.delta', { delta: '正文' }));
    expect(stream.phase.value).toBe('answering');
    expect(stream.panelExpanded.value).toBe(false);
    expect(stream.thinkingDurationMs.value).not.toBeNull();
  });

  it('maps run.failed to the error phase with a message', () => {
    const { stream, emit } = setup();
    emit(event('message.thinking.delta', { delta: '思考' }));
    emit(event('run.failed', { error_code: 'LLM_TIMEOUT', message: '上游超时', retryable: true }));
    expect(stream.phase.value).toBe('error');
    expect(stream.errorMessage.value).toBe('上游超时');
  });

  it('reset clears all buffers and phase', () => {
    const { stream, emit } = setup();
    emit(event('message.thinking.delta', { delta: '思考' }));
    emit(event('message.delta', { delta: '正文' }));
    stream.reset();
    expect(stream.phase.value).toBe('idle');
    expect(stream.thinkingText.value).toBe('');
    expect(stream.answerText.value).toBe('');
    expect(stream.thinkingDurationMs.value).toBeNull();
  });
});
