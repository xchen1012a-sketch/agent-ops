<script setup lang="ts">
import { computed } from 'vue';

import { useThemeStore, type ThemePreference } from '@stores/theme';
import { useToastStore } from '@stores/toast';

const theme = useThemeStore();
const toast = useToastStore();

const options: Array<{ value: ThemePreference; label: string }> = [
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色 (beta)' },
  { value: 'system', label: '跟随系统' },
];

const current = computed({
  get: () => theme.preference,
  set: (next: ThemePreference) => {
    theme.setPreference(next);
    toast.success(
      `主题已切换为 ${next === 'system' ? '跟随系统' : next === 'dark' ? '深色' : '浅色'}`,
    );
  },
});
</script>

<template>
  <div class="settings-page">
    <h1>偏好设置</h1>
    <el-form label-position="top">
      <el-form-item label="主题">
        <el-radio-group v-model="current">
          <el-radio v-for="opt in options" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 720px;
  margin: var(--space-8) auto;
  padding: var(--space-6);
}
</style>
