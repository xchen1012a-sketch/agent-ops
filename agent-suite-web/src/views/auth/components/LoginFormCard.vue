<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus';
import { reactive, ref } from 'vue';

import AppIcon from '@components/ui/AppIcon.vue';

interface LoginForm {
  email: string;
  password: string;
}

const props = defineProps<{
  submitting: boolean;
}>();

const emit = defineEmits<{
  (event: 'submit', value: LoginForm): void;
}>();

const formRef = ref<FormInstance | null>(null);

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

async function submitForm(): Promise<void> {
  if (props.submitting || !formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;
  emit('submit', {
    email: form.email.trim(),
    password: form.password,
  });
}
</script>

<template>
  <section class="login-form-card" aria-label="登录表单">
    <el-form
      ref="formRef"
      class="login-form-card__form"
      :model="form"
      :rules="rules"
      label-position="top"
      @submit.prevent="submitForm"
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
        />
      </el-form-item>
      <el-button
        type="primary"
        native-type="submit"
        size="large"
        class="login-form-card__submit"
        :loading="props.submitting"
      >
        登录并进入工作台
        <AppIcon name="Expand" />
      </el-button>
    </el-form>

    <el-alert
      class="login-form-card__hint"
      title="本地开发可使用已初始化的测试账号"
      type="info"
      :closable="false"
      show-icon
    />
  </section>
</template>

<style scoped>
.login-form-card {
  display: grid;
  gap: var(--space-4);
  width: 100%;
  max-width: none;
  padding: 0;
}

.login-form-card__form {
  display: grid;
  gap: var(--space-1);
}

.login-form-card__form :deep(.el-form-item) {
  min-height: 88px;
  margin-bottom: 0;
}

.login-form-card__form :deep(.el-form-item__label) {
  padding-bottom: var(--space-2);
  font-weight: 700;
}

.login-form-card__form :deep(.el-input__wrapper) {
  min-height: 50px;
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  box-shadow: 0 0 0 1px var(--color-border) inset;
  transition:
    border-color var(--duration-fast) var(--ease-in-out),
    box-shadow var(--duration-fast) var(--ease-in-out),
    background-color var(--duration-fast) var(--ease-in-out);
}

.login-form-card__form :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary);
  box-shadow:
    0 0 0 3px var(--color-primary-soft),
    0 0 0 1px var(--color-primary) inset;
}

.login-form-card__form :deep(.el-form-item__error) {
  padding-top: 5px;
}

.login-form-card__submit {
  width: 100%;
  min-height: 48px;
  margin-top: var(--space-2);
  border-radius: var(--radius-lg);
  font-weight: 700;
}

.login-form-card__submit :deep(.app-icon) {
  margin-left: var(--space-2);
}

.login-form-card__hint {
  border: 0;
  border-radius: var(--radius-lg);
}

.login-form-card__hint :deep(.el-alert__title) {
  font-size: var(--text-xs);
}

@media (max-width: 767px) {
  .login-form-card {
    max-width: none;
  }
}
</style>
