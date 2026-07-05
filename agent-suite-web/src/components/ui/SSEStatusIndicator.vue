<script setup lang="ts">
import type { StreamState } from '@/types/sse';

interface Props {
  state: StreamState;
}

defineProps<Props>();

const STATUS_META: Record<StreamState, { label: string; tone: string }> = {
  idle: { label: '空闲', tone: 'muted' },
  connecting: { label: '连接中', tone: 'info' },
  open: { label: '接收中', tone: 'success' },
  reconnecting: { label: '重连中', tone: 'warning' },
  closed: { label: '已停止', tone: 'muted' },
  error: { label: '连接异常', tone: 'danger' },
};
</script>

<template>
  <span
    class="sse-status"
    :class="`sse-status--${STATUS_META[state].tone}`"
    role="status"
    :aria-label="`流式状态: ${STATUS_META[state].label}`"
  >
    <span class="sse-status__dot" aria-hidden="true" />
    {{ STATUS_META[state].label }}
  </span>
</template>

<style scoped>
.sse-status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 2px var(--space-2);
  font-size: var(--text-xs);
  border-radius: var(--radius-pill);
  background-color: var(--color-surface-muted);
}

.sse-status__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: currentColor;
}

.sse-status--success {
  color: var(--color-success);
  background-color: var(--color-success-soft);
}

.sse-status--warning {
  color: var(--color-warning);
  background-color: var(--color-warning-soft);
}

.sse-status--danger {
  color: var(--color-danger);
  background-color: var(--color-danger-soft);
}

.sse-status--info {
  color: var(--color-info);
  background-color: var(--color-info-soft);
}

.sse-status--muted {
  color: var(--color-text-muted);
}

.sse-status--success .sse-status__dot,
.sse-status--info .sse-status__dot {
  animation: sse-status__pulse 1.5s ease-in-out infinite;
}

@keyframes sse-status__pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.4);
    opacity: 0.6;
  }
}
</style>
