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
    <el-icon class="loading-state__spinner" :size="props.fullscreen ? 32 : 24">
      <Loading />
    </el-icon>
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
  background-color: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(2px);
  flex-direction: column;
  gap: var(--space-3);
}

:root[data-theme='dark'] .loading-state--fullscreen {
  background-color: rgba(15, 23, 42, 0.6);
}

.loading-state__spinner {
  animation: loading-state__spin 1s linear infinite;
}

@keyframes loading-state__spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
