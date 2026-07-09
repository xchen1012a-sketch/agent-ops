<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';
import type { FormInstance, FormRules } from 'element-plus';

interface PasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const router = useRouter();
const auth = useAuthStore();
const toast = useToastStore();

const formRef = ref<FormInstance | null>(null);
const submitting = ref(false);

const form = reactive<PasswordForm>({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
});

const validateConfirm = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'));
    return;
  }
  callback();
};

const rules: FormRules<PasswordForm> = {
  currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少 8 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
};

const profileRows = computed(() => [
  { label: '邮箱', value: auth.profile?.email ?? '-' },
  { label: '显示名', value: auth.profile?.display_name ?? '-' },
  { label: '角色', value: auth.role === 'admin' ? '管理员' : '普通用户' },
]);

async function handleSubmit(): Promise<void> {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  submitting.value = true;
  try {
    await auth.changePassword({
      current_password: form.currentPassword,
      new_password: form.newPassword,
      confirm_password: form.confirmPassword,
    });
    toast.success('密码已更新，请使用新密码重新登录');
    await router.push({ name: 'login' });
  } catch (error) {
    const message = error instanceof Error ? error.message : '修改密码失败';
    toast.error(message);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="profile-page">
    <h1>个人信息</h1>
    <el-descriptions :column="1" border>
      <el-descriptions-item v-for="row in profileRows" :key="row.label" :label="row.label">
        {{ row.value }}
      </el-descriptions-item>
    </el-descriptions>

    <h2>修改密码</h2>
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="profile-page__form"
    >
      <el-form-item label="当前密码" prop="currentPassword">
        <el-input v-model="form.currentPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" prop="newPassword">
        <el-input v-model="form.newPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认新密码" prop="confirmPassword">
        <el-input v-model="form.confirmPassword" type="password" show-password />
      </el-form-item>
      <el-button type="primary" :loading="submitting" @click="handleSubmit"> 更新密码 </el-button>
    </el-form>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 720px;
  margin: var(--space-8) auto;
  padding: var(--space-6);
}

.profile-page__form {
  margin-top: var(--space-4);
}
</style>
