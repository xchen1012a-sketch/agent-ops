<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import type { AgentApiConfigUpdate, AgentApiConfigView } from '@/types/admin-api-config';

interface Props {
  modelValue: boolean;
  config: AgentApiConfigView | null;
  saving: boolean;
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void;
  (e: 'submit', payload: AgentApiConfigUpdate): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const form = ref<AgentApiConfigUpdate>(emptyForm());

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

watch(
  () => props.config,
  (config) => {
    if (!config) return;
    form.value = {
      display_name: config.display_name,
      base_url: config.base_url,
      model: config.model,
      api_key: null,
      timeout_seconds: config.timeout_seconds,
      max_retries: config.max_retries,
      enabled: config.enabled,
      extra: config.extra,
    };
  },
);

function emptyForm(): AgentApiConfigUpdate {
  return {
    display_name: '',
    base_url: null,
    model: null,
    api_key: null,
    timeout_seconds: null,
    max_retries: null,
    enabled: true,
    extra: null,
  };
}

function submit(): void {
  emit('submit', { ...form.value });
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`编辑 ${config?.display_name ?? ''} 配置`"
    width="560px"
    :close-on-click-modal="false"
  >
    <el-form v-if="config" :model="form" label-width="120px" label-position="right">
      <el-form-item label="显示名称">
        <el-input v-model="form.display_name" />
      </el-form-item>
      <el-form-item label="Base URL">
        <el-input v-model="form.base_url" placeholder="https://..." />
      </el-form-item>
      <el-form-item label="模型">
        <el-input v-model="form.model" placeholder="如 deepseek-chat" />
      </el-form-item>
      <el-form-item label="API Key">
        <el-input
          v-model="form.api_key"
          type="password"
          show-password
          :placeholder="
            config.api_key_hint ? `当前 ${config.api_key_hint}，不改请留空` : '输入新 key'
          "
        />
      </el-form-item>
      <el-form-item label="超时(秒)">
        <el-input-number v-model="form.timeout_seconds" :min="1" :max="600" />
      </el-form-item>
      <el-form-item label="重试次数">
        <el-input-number v-model="form.max_retries" :min="0" :max="10" />
      </el-form-item>
      <el-form-item label="启用">
        <el-switch v-model="form.enabled" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>
