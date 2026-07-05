<script setup lang="ts" generic="T">
import type { RequestState } from '@/types/request-state';

import EmptyState from './EmptyState.vue';
import LoadingState from './LoadingState.vue';
import RetryAction from './RetryAction.vue';

interface Props {
  state: RequestState<T>;
  loadingMessage?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionText?: string;
  retrying?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loadingMessage: '加载中…',
  emptyTitle: '暂无数据',
  emptyDescription: '',
  emptyActionText: '',
  retrying: false,
});

const emit = defineEmits<{
  (e: 'retry'): void;
  (e: 'empty-action'): void;
}>();
</script>

<template>
  <LoadingState v-if="props.state.status === 'loading'" :message="props.loadingMessage" />

  <RetryAction
    v-else-if="props.state.status === 'error' && props.state.error"
    :error="props.state.error"
    :loading="props.retrying"
    @retry="emit('retry')"
  />

  <EmptyState
    v-else-if="props.state.status === 'empty'"
    :title="props.emptyTitle"
    :description="props.emptyDescription"
    :action-text="props.emptyActionText"
    @action="emit('empty-action')"
  />

  <slot v-else-if="props.state.status === 'success'" :data="props.state.data" />

  <slot v-else-if="props.state.status === 'cancelled'" name="cancelled">
    <RetryAction
      v-if="props.state.error"
      :error="props.state.error"
      :loading="props.retrying"
      @retry="emit('retry')"
    />
  </slot>

  <slot v-else name="idle" />
</template>
