<script setup lang="ts">
interface Props {
  message?: string;
  fullscreen?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  message: '加载中…',
  fullscreen: false,
});
</script>

<template>
  <div
    class="loading-state"
    :class="{ 'loading-state--fullscreen': props.fullscreen }"
    role="status"
    aria-live="polite"
  >
    <span class="loading-state__spinner" aria-hidden="true" />
    <span class="loading-state__message">{{ props.message }}</span>
  </div>
</template>

<style scoped>
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-6);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.loading-state--fullscreen {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal-backdrop);
  background-color: color-mix(in oklch, var(--color-surface-glass), transparent 12%);
  flex-direction: column;
  gap: var(--space-3);
}

:root[data-theme='dark'] .loading-state--fullscreen {
  background-color: color-mix(in oklch, var(--color-surface-glass), transparent 8%);
}

.loading-state__spinner {
  width: 1.5em;
  height: 1.5em;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: loading-state__spin 1s linear infinite;
}

@keyframes loading-state__spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
