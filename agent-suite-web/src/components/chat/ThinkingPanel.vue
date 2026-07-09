<script setup lang="ts">
import { computed, nextTick, ref, toRef, watch } from 'vue';

import { useTypewriter } from '@/composables/useTypewriter';
import type { StreamPhase } from '@/composables/useAgentStream';

/**
 * ThinkingPanel (STREAM-100).
 *
 * Claude.ai-style collapsible reasoning panel. Presentational only: it receives
 * the raw thinking buffer + phase and renders a typewriter-scrolled panel that
 * auto-collapses when answering starts and shows "已思考 X 秒". No business or
 * agent-specific logic, so it is copyable across the three agent frontends.
 *
 * Accent color is driven by the `tone` prop through the `--tp-accent` custom
 * property, which maps to the per-agent theme token (legal/recruit/data) and
 * therefore adapts to dark mode automatically.
 */
interface Props {
  thinking: string;
  phase: StreamPhase;
  elapsedSeconds: number;
  durationMs: number | null;
  expanded: boolean;
  tone?: 'legal' | 'recruit' | 'data' | 'default';
}

const props = withDefaults(defineProps<Props>(), {
  tone: 'default',
});

const emit = defineEmits<{ (event: 'toggle'): void }>();

const { displayed } = useTypewriter(toRef(props, 'thinking'), { charsPerTick: 3, intervalMs: 24 });

const scrollBody = ref<HTMLElement | null>(null);

const isThinking = computed(() => props.phase === 'thinking');
const hasThinking = computed(() => props.thinking.trim().length > 0);

const doneLabel = computed(() => {
  const seconds =
    props.durationMs !== null
      ? Math.max(1, Math.round(props.durationMs / 1000))
      : props.elapsedSeconds;
  return seconds > 0 ? `已思考 ${seconds} 秒` : '已完成思考';
});

watch(
  () => displayed.value,
  async () => {
    if (!props.expanded) return;
    await nextTick();
    const body = scrollBody.value;
    if (body) body.scrollTop = body.scrollHeight;
  },
);
</script>

<template>
  <section
    v-if="hasThinking"
    class="thinking-panel"
    :class="[`thinking-panel--${tone}`, { 'thinking-panel--active': isThinking }]"
  >
    <button
      type="button"
      class="thinking-panel__header"
      :aria-expanded="expanded"
      @click="emit('toggle')"
    >
      <span class="thinking-panel__spark" :class="{ 'is-spinning': isThinking }" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="15" height="15" focusable="false">
          <path
            d="M12 1.5 L13.8 9.3 L21.6 11.1 L13.8 12.9 L12 20.7 L10.2 12.9 L2.4 11.1 L10.2 9.3 Z"
            fill="currentColor"
          />
        </svg>
      </span>

      <span v-if="isThinking" class="thinking-panel__label thinking-panel__label--live">
        Thinking
      </span>
      <span v-else class="thinking-panel__label">{{ doneLabel }}</span>

      <span v-if="isThinking" class="thinking-panel__dots" aria-hidden="true">
        <i style="animation-delay: 0s" />
        <i style="animation-delay: 0.2s" />
        <i style="animation-delay: 0.4s" />
      </span>

      <span class="thinking-panel__chevron" :class="{ 'is-open': expanded }" aria-hidden="true">
        ›
      </span>
    </button>

    <div v-show="expanded" ref="scrollBody" class="thinking-panel__body" role="note">
      <p class="thinking-panel__text">{{ displayed }}</p>
    </div>
  </section>
</template>

<style scoped>
.thinking-panel {
  --tp-accent: var(--color-primary);
  margin-bottom: var(--space-3);
}

.thinking-panel--legal {
  --tp-accent: var(--color-legal);
}

.thinking-panel--recruit {
  --tp-accent: var(--color-recruit);
}

.thinking-panel--data {
  --tp-accent: var(--color-data);
}

.thinking-panel__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-1) 0;
  color: var(--color-text-muted);
  background: transparent;
  border: 0;
  font-size: var(--text-sm);
  font-weight: 500;
  text-align: left;
  cursor: pointer;
}

.thinking-panel__spark {
  display: inline-flex;
  color: var(--tp-accent);
}

.thinking-panel__spark.is-spinning {
  animation: thinking-panel-spark 1.8s ease-in-out infinite;
}

.thinking-panel__label {
  color: var(--color-text-secondary, var(--color-text-muted));
}

.thinking-panel__label--live {
  font-weight: 500;
  background: linear-gradient(
    90deg,
    var(--color-text-subtle) 25%,
    var(--tp-accent) 50%,
    var(--color-text-subtle) 75%
  );
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: thinking-panel-shimmer 2s linear infinite;
}

.thinking-panel__dots {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.thinking-panel__dots i {
  width: 4px;
  height: 4px;
  border-radius: var(--radius-pill);
  background: var(--tp-accent);
  animation: thinking-panel-bob 1.4s ease-in-out infinite;
}

.thinking-panel__chevron {
  margin-left: auto;
  color: var(--color-text-subtle);
  transition: transform 0.18s ease;
  transform: rotate(90deg);
}

.thinking-panel__chevron.is-open {
  transform: rotate(-90deg);
}

.thinking-panel__body {
  max-height: 240px;
  margin-top: var(--space-2);
  padding: 0 0 var(--space-1) var(--space-3);
  border-left: 1.5px solid var(--tp-accent);
  border-radius: 0;
  overflow-y: auto;
  -webkit-mask-image: linear-gradient(to bottom, transparent, #000 22px);
  mask-image: linear-gradient(to bottom, transparent, #000 22px);
}

.thinking-panel__text {
  margin: 0;
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  line-height: var(--line-relaxed);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

@keyframes thinking-panel-spark {
  0%,
  100% {
    transform: rotate(0deg) scale(1);
    opacity: 0.75;
  }
  50% {
    transform: rotate(90deg) scale(1.18);
    opacity: 1;
  }
}

@keyframes thinking-panel-shimmer {
  to {
    background-position: -200% 0;
  }
}

@keyframes thinking-panel-bob {
  0%,
  100% {
    opacity: 0.25;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .thinking-panel__spark.is-spinning,
  .thinking-panel__label--live,
  .thinking-panel__dots i {
    animation: none;
  }
  .thinking-panel__label--live {
    background: none;
    -webkit-text-fill-color: currentColor;
    color: var(--tp-accent);
  }
}
</style>
