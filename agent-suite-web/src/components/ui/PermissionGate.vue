<script setup lang="ts">
import { computed } from 'vue';

import { useAuthStore } from '@stores/auth';

interface Props {
  role?: 'admin' | 'user';
  fallback?: 'hidden' | 'forbidden';
}

const props = withDefaults(defineProps<Props>(), {
  fallback: 'hidden',
  role: undefined,
});

const auth = useAuthStore();

const allowed = computed(() => {
  if (!props.role) return auth.isAuthenticated;
  return auth.role === props.role;
});
</script>

<template>
  <template v-if="allowed">
    <slot />
  </template>
  <slot v-else name="fallback">
    <div v-if="fallback === 'forbidden'" class="permission-gate__fallback" role="alert">
      <p>当前账号无权访问该内容。</p>
    </div>
  </slot>
</template>

<style scoped>
.permission-gate__fallback {
  padding: var(--space-6);
  background-color: var(--color-warning-soft);
  border-radius: var(--radius-md);
  color: var(--color-warning);
  font-size: var(--text-sm);
}
</style>
