<script setup lang="ts">
import { onErrorCaptured, ref } from 'vue';

import { useToastStore } from '@stores/toast';

interface BoundaryError {
  message: string;
  stack?: string;
  capturedAt: number;
}

const error = ref<BoundaryError | null>(null);
const toast = useToastStore();

onErrorCaptured((captured) => {
  const message = captured instanceof Error ? captured.message : String(captured);
  error.value = {
    message,
    stack: captured instanceof Error ? captured.stack : undefined,
    capturedAt: Date.now(),
  };
  toast.error('页面运行异常，请刷新或返回上一页', '运行错误');
  console.error('[error-boundary]', captured);
  return false;
});

function reload(): void {
  error.value = null;
  if (typeof window !== 'undefined') {
    window.location.reload();
  }
}

function reset(): void {
  error.value = null;
}
</script>

<template>
  <div v-if="error" class="error-boundary" role="alert">
    <h2 class="error-boundary__title">页面运行出现异常</h2>
    <p class="error-boundary__message">
      {{ error.message }}
    </p>
    <pre v-if="error.stack" class="error-boundary__stack">{{ error.stack }}</pre>
    <div class="error-boundary__actions">
      <el-button type="primary" @click="reload"> 刷新页面 </el-button>
      <el-button @click="reset"> 尝试继续 </el-button>
    </div>
  </div>
  <slot v-else />
</template>

<style scoped>
.error-boundary {
  max-width: 720px;
  margin: var(--space-12) auto;
  padding: var(--space-8);
  background-color: var(--color-surface);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.error-boundary__title {
  margin-bottom: var(--space-3);
  color: var(--color-danger);
  font-size: var(--text-xl);
}

.error-boundary__message {
  margin-bottom: var(--space-4);
  color: var(--color-text);
}

.error-boundary__stack {
  padding: var(--space-3);
  margin-bottom: var(--space-4);
  background-color: var(--color-surface-muted);
  border-radius: var(--radius-md);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  overflow-x: auto;
}

.error-boundary__actions {
  display: flex;
  gap: var(--space-3);
}
</style>
