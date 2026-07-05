<script setup lang="ts">
import AppIcon from '@components/ui/AppIcon.vue';

const emit = defineEmits<{
  (event: 'login'): void;
}>();
</script>

<template>
  <header class="login-top-bar" aria-label="顶部导航">
    <div class="login-top-bar__brand" aria-label="Agent Suite">
      <span class="login-top-bar__brand-mark" aria-hidden="true">
        <AppIcon name="ChatDotRound" />
      </span>
      <span>
        <strong>Agent Suite</strong>
        <small>Enterprise AI</small>
      </span>
    </div>

    <el-button class="login-top-bar__login" type="primary" round @click="emit('login')">
      登录
      <span aria-hidden="true">↗</span>
    </el-button>
  </header>
</template>

<style scoped>
.login-top-bar {
  position: fixed;
  top: var(--space-4);
  left: 50%;
  z-index: var(--z-fixed);
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: var(--space-4);
  width: min(calc(100% - var(--space-8)), 1120px);
  min-height: 64px;
  padding: var(--space-2) var(--space-3) var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--login-border);
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow-card);
  transform: translateX(-50%);
}

.login-top-bar__brand {
  display: flex;
  align-items: center;
}

.login-top-bar__brand {
  gap: var(--space-3);
  min-width: 0;
  color: var(--login-text);
}

.login-top-bar__brand > span:last-child {
  display: grid;
  gap: 1px;
}

.login-top-bar__brand strong {
  font-size: var(--text-sm);
}

.login-top-bar__brand small {
  color: var(--login-text-subtle);
  font-family: var(--font-mono);
  font-size: 0.625rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.login-top-bar__brand-mark {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 36px;
  height: 36px;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid color-mix(in oklch, var(--color-primary) 28%, var(--color-border));
  border-radius: var(--radius-md);
  box-shadow: none;
}

.login-top-bar__login {
  justify-self: end;
  min-width: 96px;
  min-height: 44px;
  color: var(--color-text-inverse);
  font-weight: 720;
}

.login-top-bar__login:hover {
  color: var(--color-text-inverse);
}

.login-top-bar__login span {
  margin-left: var(--space-2);
}

@media (max-width: 767px) {
  .login-top-bar {
    top: var(--space-3);
    grid-template-columns: 1fr auto;
    width: calc(100% - var(--space-6));
    min-height: 60px;
  }

  .login-top-bar__brand small {
    display: none;
  }
}
</style>
