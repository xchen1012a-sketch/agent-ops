<script setup lang="ts">
import { computed } from 'vue';

import { useToastStore } from '@stores/toast';
import AppIcon from '@components/ui/AppIcon.vue';

const toast = useToastStore();
const items = computed(() => toast.items);
const notificationLabel = '\u901a\u77e5';
const closeNotificationLabel = '\u5173\u95ed\u901a\u77e5';
</script>

<template>
  <Teleport to="body">
    <div class="global-toast" role="region" :aria-label="notificationLabel" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="item in items"
          :key="item.id"
          class="global-toast__item"
          :class="`global-toast__item--${item.type}`"
          role="alert"
        >
          <el-icon class="global-toast__icon">
            <AppIcon
              :name="
                item.type === 'success'
                  ? 'CircleCheck'
                  : item.type === 'warning'
                    ? 'Warning'
                    : item.type === 'error'
                      ? 'CircleClose'
                      : 'InfoFilled'
              "
            />
          </el-icon>
          <div class="global-toast__body">
            <strong v-if="item.title" class="global-toast__title">{{ item.title }}</strong>
            <p class="global-toast__message">
              {{ item.message }}
            </p>
          </div>
          <button
            type="button"
            class="global-toast__close"
            :aria-label="`${closeNotificationLabel}: ${item.title ?? item.message}`"
            @click="toast.dismiss(item.id)"
          >
            <el-icon><AppIcon name="Close" /></el-icon>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.global-toast {
  position: fixed;
  top: var(--space-4);
  right: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  z-index: var(--z-toast);
  pointer-events: none;
}

.global-toast__item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  min-width: 280px;
  max-width: 480px;
  padding: var(--space-3) var(--space-4);
  background-color: var(--color-surface);
  border-left: 4px solid var(--color-info);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-popover);
  pointer-events: auto;
}

.global-toast__item--success {
  border-left-color: var(--color-success);
}
.global-toast__item--warning {
  border-left-color: var(--color-warning);
}
.global-toast__item--error {
  border-left-color: var(--color-danger);
}

.global-toast__icon {
  flex: 0 0 auto;
  margin-top: 2px;
}

.global-toast__item--success .global-toast__icon {
  color: var(--color-success);
}
.global-toast__item--warning .global-toast__icon {
  color: var(--color-warning);
}
.global-toast__item--error .global-toast__icon {
  color: var(--color-danger);
}
.global-toast__item--info .global-toast__icon {
  color: var(--color-info);
}

.global-toast__body {
  flex: 1 1 auto;
}

.global-toast__title {
  display: block;
  margin-bottom: 2px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.global-toast__message {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  word-break: break-word;
}

.global-toast__close {
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
  border: none;
  background-color: transparent;
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out);
}

.global-toast__close:hover {
  background-color: var(--color-surface-muted);
  color: var(--color-text);
}

.toast-enter-active,
.toast-leave-active {
  transition: all var(--duration-normal) var(--ease-in-out);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(24px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(24px);
}
</style>
