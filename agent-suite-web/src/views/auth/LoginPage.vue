<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';
import type { LoginCredentials } from '@/types/auth';

import LoginDialog from './components/LoginDialog.vue';
import LoginProductIntro from './components/LoginProductIntro.vue';
import LoginTopBar from './components/LoginTopBar.vue';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const toast = useToastStore();

const submitting = ref(false);
const loginDialogVisible = ref(false);

const redirectTarget = computed(() => {
  const redirect = route.query.redirect;
  return typeof redirect === 'string' ? redirect : '/legal';
});

async function handleLogin(credentials: LoginCredentials): Promise<void> {
  if (submitting.value) return;
  submitting.value = true;
  try {
    await auth.login(credentials);
    toast.success('登录成功');
    loginDialogVisible.value = false;
    await router.push(redirectTarget.value);
  } catch (error) {
    const message = error instanceof Error ? error.message : '登录失败，请重试';
    toast.error(message);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="login-page" aria-label="Agent Suite 产品介绍">
    <div class="login-page__background" aria-hidden="true">
      <span class="login-page__grid" />
    </div>

    <LoginTopBar @login="loginDialogVisible = true" />
    <div class="login-page__content">
      <LoginProductIntro @login="loginDialogVisible = true" />
    </div>
    <LoginDialog v-model="loginDialogVisible" :submitting="submitting" @submit="handleLogin" />
  </main>
</template>

<style scoped>
.login-page {
  --login-canvas: var(--color-bg);
  --login-canvas-deep: color-mix(in oklch, var(--color-bg) 90%, var(--color-primary-soft));
  --login-surface: color-mix(in oklch, var(--color-surface) 78%, transparent);
  --login-surface-strong: var(--color-surface);
  --login-border: var(--color-border);
  --login-border-strong: color-mix(in oklch, var(--color-primary) 24%, var(--color-border));
  --login-text: var(--color-text);
  --login-text-muted: var(--color-text-muted);
  --login-text-subtle: var(--color-text-subtle);
  --login-accent: var(--color-primary);

  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    linear-gradient(
      135deg,
      color-mix(in oklch, var(--color-primary-soft), transparent 68%),
      transparent 42%
    ),
    linear-gradient(145deg, var(--login-canvas), var(--login-canvas-deep));
}

.login-page__background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.login-page__grid {
  position: absolute;
  inset: 0;
  opacity: 0.18;
  background-image:
    linear-gradient(var(--login-border) 1px, transparent 1px),
    linear-gradient(90deg, var(--login-border) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(to bottom, black, transparent 76%);
}
.login-page__content {
  position: relative;
  z-index: var(--z-base);
  width: min(100%, 1280px);
  min-height: 100vh;
  margin: 0 auto;
  padding: 108px clamp(var(--space-5), 4vw, var(--space-12)) var(--space-10);
}

@media (max-width: 1023px) {
  .login-page {
    overflow: auto;
  }
  .login-page__content {
    min-height: auto;
    padding-top: 102px;
  }
}

@media (max-width: 767px) {
  .login-page__content {
    padding: 92px var(--space-5) var(--space-8);
  }
}
</style>
