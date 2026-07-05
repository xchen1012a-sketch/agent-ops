<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';

const router = useRouter();
const auth = useAuthStore();
const toast = useToastStore();

onMounted(async () => {
  try {
    await auth.logout();
    toast.success('已退出登录');
  } catch (error) {
    console.error('[logout]', error);
  } finally {
    await router.replace({ name: 'login' });
  }
});
</script>

<template>
  <div class="logout-page" role="status" aria-live="polite">
    <p>正在退出登录…</p>
  </div>
</template>

<style scoped>
.logout-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: var(--color-text-muted);
}
</style>
