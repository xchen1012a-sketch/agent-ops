import { getCurrentScope, onScopeDispose, ref, watch, type Ref } from 'vue';

/**
 * Typewriter composable (STREAM-100).
 *
 * Decouples the "received" buffer from the "displayed" buffer so streamed text
 * reveals character-by-character regardless of how fast chunks arrive. Business
 * and model agnostic — copyable across the three agent frontends.
 */
export interface UseTypewriterOptions {
  /** Characters revealed per tick. Default 2. */
  charsPerTick?: number;
  /** Tick interval in milliseconds. Default 16 (~60fps). */
  intervalMs?: number;
}

export interface UseTypewriterReturn {
  /** The progressively revealed text. */
  displayed: Ref<string>;
  /** Reveal everything immediately (e.g. on completion or user skip). */
  flush: () => void;
}

export function useTypewriter(
  source: Ref<string>,
  options: UseTypewriterOptions = {},
): UseTypewriterReturn {
  const charsPerTick = Math.max(1, options.charsPerTick ?? 2);
  const intervalMs = Math.max(1, options.intervalMs ?? 16);

  const displayed = ref('');
  let timer: ReturnType<typeof setInterval> | null = null;

  function stopTimer(): void {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  }

  function tick(): void {
    const target = source.value;
    if (displayed.value.length >= target.length) {
      stopTimer();
      return;
    }
    // If the source diverged (reset to a shorter/different string), restart.
    if (!target.startsWith(displayed.value)) {
      displayed.value = '';
    }
    const nextLength = Math.min(target.length, displayed.value.length + charsPerTick);
    displayed.value = target.slice(0, nextLength);
    if (displayed.value.length >= target.length) {
      stopTimer();
    }
  }

  function ensureTimer(): void {
    if (timer === null) {
      timer = setInterval(tick, intervalMs);
    }
  }

  function flush(): void {
    stopTimer();
    displayed.value = source.value;
  }

  watch(
    source,
    (value) => {
      if (value === '') {
        stopTimer();
        displayed.value = '';
        return;
      }
      if (!value.startsWith(displayed.value)) {
        displayed.value = '';
      }
      if (displayed.value.length < value.length) {
        ensureTimer();
      }
    },
    { immediate: true },
  );

  if (getCurrentScope()) {
    onScopeDispose(stopTimer);
  }

  return { displayed, flush };
}
