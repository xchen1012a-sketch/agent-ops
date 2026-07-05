<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

function goHome(): void {
  void router.push({ name: 'legal-sessions' });
}
</script>

<template>
  <div class="not-found-page">
    <h1 class="not-found-page__code">404</h1>
    <p class="not-found-page__title">页面未找到</p>
    <p class="not-found-page__hint">您访问的页面不存在或已被移动。</p>
    <el-button type="primary" @click="goHome"> 返回首页 </el-button>
  </div>
</template>

<style scoped>
.not-found-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: var(--space-3);
  text-align: center;
}

.not-found-page__code {
  font-size: 96px;
  margin: 0;
  color: var(--color-primary);
  font-weight: 700;
}

.not-found-page__title {
  font-size: var(--text-xl);
  color: var(--color-text);
  margin: 0;
}

.not-found-page__hint {
  color: var(--color-text-muted);
  margin: 0 0 var(--space-4);
}
</style>
