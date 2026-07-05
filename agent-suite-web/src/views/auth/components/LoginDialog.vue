<script setup lang="ts">
import type { LoginCredentials } from '@/types/auth';
import AppIcon from '@components/ui/AppIcon.vue';

import LoginFormCard from './LoginFormCard.vue';

const props = defineProps<{
  modelValue: boolean;
  submitting: boolean;
}>();

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void;
  (event: 'submit', value: LoginCredentials): void;
}>();

function updateVisible(value: boolean): void {
  emit('update:modelValue', value);
}
</script>

<template>
  <el-dialog
    :model-value="props.modelValue"
    width="min(92vw, 500px)"
    align-center
    destroy-on-close
    class="login-dialog"
    :show-close="false"
    @update:model-value="updateVisible"
  >
    <template #header>
      <div class="login-dialog__header">
        <div class="login-dialog__brand">
          <span class="login-dialog__brand-mark" aria-hidden="true">
            <AppIcon name="ChatDotRound" />
          </span>
          <span>
            <strong>Agent Suite</strong>
            <small>安全登录</small>
          </span>
        </div>
        <el-button
          class="login-dialog__close"
          text
          circle
          aria-label="关闭登录弹窗"
          @click="updateVisible(false)"
        >
          <AppIcon name="Close" />
        </el-button>
      </div>
    </template>

    <div class="login-dialog__intro">
      <h2>继续你的 AI 工作流</h2>
      <p>登录后即可访问法律、招聘与数据专家。</p>
    </div>

    <LoginFormCard :submitting="props.submitting" @submit="emit('submit', $event)" />
  </el-dialog>
</template>

<style scoped>
.login-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.login-dialog__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.login-dialog__brand > span:last-child {
  display: grid;
  gap: 1px;
}

.login-dialog__brand strong {
  color: var(--color-text);
  font-size: var(--text-sm);
}

.login-dialog__brand small {
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.login-dialog__brand-mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid color-mix(in oklch, var(--color-primary) 28%, var(--color-border));
  border-radius: var(--radius-md);
  box-shadow: none;
}

.login-dialog__close {
  width: 40px;
  height: 40px;
  color: var(--color-text-muted);
  font-size: var(--text-lg);
}

.login-dialog__close:hover {
  color: var(--color-text);
  background: var(--color-surface-muted);
}

.login-dialog__intro {
  display: grid;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
}

.login-dialog__intro h2 {
  font-size: var(--text-2xl);
  font-weight: 760;
  letter-spacing: 0;
}

.login-dialog__intro p {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

:deep(.el-dialog) {
  position: relative;
  min-height: 550px;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: calc(var(--radius-xl) + 4px);
  box-shadow: var(--shadow-modal);
}

:deep(.el-dialog::before) {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 3px;
  content: '';
  background: var(--color-primary);
}

:deep(.el-overlay-dialog) {
  overflow: auto;
  overscroll-behavior: contain;
}

:deep(.el-dialog__header) {
  padding: var(--space-6) var(--space-8) var(--space-5);
}

:deep(.el-dialog__body) {
  padding: 0 var(--space-8) var(--space-8);
}

@media (max-height: 620px) {
  :deep(.el-dialog) {
    min-height: 0;
    margin-block: var(--space-4);
  }
}

@media (max-width: 520px) {
  :deep(.el-dialog__header) {
    padding: var(--space-5) var(--space-5) var(--space-4);
  }

  :deep(.el-dialog__body) {
    padding: 0 var(--space-5) var(--space-5);
  }
}
</style>
