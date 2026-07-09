<script setup lang="ts">
import type { RequestErrorView } from '@/types/request-state';

interface Props {
  error: RequestErrorView;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

const emit = defineEmits<{ (e: 'retry'): void }>();
</script>

<template>
  <div class="retry-action" :class="`retry-action--${props.error.tone}`" role="alert">
    <div class="retry-action__content">
      <strong class="retry-action__title">{{ props.error.title }}</strong>
      <p class="retry-action__message">{{ props.error.message }}</p>
      <p v-if="props.error.retryAfterSeconds" class="retry-action__meta">
        建议 {{ props.error.retryAfterSeconds }} 秒后重试
      </p>
      <p v-if="props.error.traceId" class="retry-action__meta">
        追踪编号：{{ props.error.traceId }}
      </p>
    </div>
    <el-button
      v-if="props.error.retryable"
      type="primary"
      plain
      :loading="props.loading"
      @click="emit('retry')"
    >
      {{ props.error.actionLabel }}
    </el-button>
  </div>
</template>

<style scoped>
.retry-action {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
}

.retry-action--info {
  border-color: var(--color-info-soft);
}

.retry-action--warning {
  border-color: var(--color-warning-soft);
  background-color: var(--color-warning-soft);
}

.retry-action--danger {
  border-color: var(--color-danger-soft);
  background-color: var(--color-danger-soft);
}

.retry-action__content {
  min-width: 0;
}

.retry-action__title {
  display: block;
  margin-bottom: var(--space-1);
  color: var(--color-text);
  font-size: var(--text-sm);
}

.retry-action__message,
.retry-action__meta {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  overflow-wrap: anywhere;
}

.retry-action__meta {
  margin-top: var(--space-1);
  font-size: var(--text-xs);
}

@media (max-width: 520px) {
  .retry-action {
    flex-direction: column;
  }
}
</style>
