<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';
import type { FormInstance, FormRules } from 'element-plus';

interface LoginForm {
  email: string;
  password: string;
}

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const toast = useToastStore();

const formRef = ref<FormInstance | null>(null);
const submitting = ref(false);

const form = reactive<LoginForm>({
  email: '',
  password: '',
});

const rules: FormRules<LoginForm> = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少 8 位', trigger: 'blur' },
  ],
};

const redirectTarget = computed(() => {
  const redirect = route.query.redirect;
  return typeof redirect === 'string' ? redirect : '/legal';
});

async function handleSubmit(): Promise<void> {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  submitting.value = true;
  try {
    await auth.login({
      email: form.email.trim(),
      password: form.password,
    });
    toast.success('登录成功');
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
  <div class="login-page">
    <div class="login-page__card">
      <header class="login-page__header">
        <h1 class="login-page__title">企业智能体平台</h1>
        <p class="login-page__subtitle">法律咨询 · 智能招聘 · 智能问数</p>
      </header>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="form.email"
            type="email"
            autocomplete="username"
            placeholder="you@example.com"
            size="large"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            placeholder="至少 8 位"
            show-password
            size="large"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-page__submit"
          :loading="submitting"
          @click="handleSubmit"
        >
          登录
        </el-button>
      </el-form>
      <footer class="login-page__footer">
        <p>登录即表示同意平台使用条款与隐私政策。</p>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--space-6);
  background:
    radial-gradient(circle at top left, var(--color-legal-soft), transparent 50%),
    radial-gradient(circle at bottom right, var(--color-data-soft), transparent 50%),
    var(--color-bg);
}

.login-page__card {
  width: 100%;
  max-width: 420px;
  padding: var(--space-8);
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.login-page__header {
  text-align: center;
  margin-bottom: var(--space-6);
}

.login-page__title {
  margin: 0 0 var(--space-1);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
}

.login-page__subtitle {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.login-page__submit {
  width: 100%;
  margin-top: var(--space-2);
}

.login-page__footer {
  margin-top: var(--space-4);
  text-align: center;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
</style>
