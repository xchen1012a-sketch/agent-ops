<script setup lang="ts">
import { useRouter } from 'vue-router';

import { useToastStore } from '@stores/toast';

const router = useRouter();
const toast = useToastStore();

function handleSkip(): void {
  toast.info('已跳过账号初始化');
  void router.push({ name: 'legal-sessions' });
}
</script>

<template>
  <div class="onboarding-page">
    <h1>账号初始化</h1>
    <p>该页面用于飞书 open_id 首次登录后设置密码（可选）。</p>
    <el-button @click="handleSkip"> 暂不设置，直接进入 </el-button>
  </div>
</template>

<style scoped>
.onboarding-page {
  max-width: 480px;
  margin: var(--space-12) auto;
  padding: var(--space-8);
  text-align: center;
}
</style>
