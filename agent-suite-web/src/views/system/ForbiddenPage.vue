<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

function goBack(): void {
  if (window.history.length > 1) {
    void router.back();
  } else {
    void router.push({ name: 'legal-sessions' });
  }
}
</script>

<template>
  <div class="forbidden-page">
    <h1 class="forbidden-page__code">403</h1>
    <p class="forbidden-page__title">权限不足</p>
    <p class="forbidden-page__hint">当前账号无权访问该页面。</p>
    <el-button @click="goBack"> 返回上一页 </el-button>
  </div>
</template>

<style scoped>
.forbidden-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: var(--space-3);
  text-align: center;
}

.forbidden-page__code {
  font-size: 96px;
  margin: 0;
  color: var(--color-warning);
  font-weight: 700;
}

.forbidden-page__title {
  font-size: var(--text-xl);
  color: var(--color-text);
  margin: 0;
}

.forbidden-page__hint {
  color: var(--color-text-muted);
  margin: 0 0 var(--space-4);
}
</style>
