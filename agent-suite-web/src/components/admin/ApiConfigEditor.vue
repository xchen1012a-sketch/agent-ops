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

interface FeishuFields {
  app_id: string;
  app_secret: string;
  verification_token: string;
  encrypt_key: string;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const form = ref<AgentApiConfigUpdate>(emptyForm());
// FEISHU-300: 飞书 4 字段单独维护；submit 时再拼回 extra + api_key。
// app_secret 留空表示「不改」，与 api_key 行为一致；保存后服务端只回遮挡值。
const feishuFields = ref<FeishuFields>(emptyFeishuFields());

const isFeishu = computed(() => props.config?.api_type === 'feishu');
const webhookUrl = computed(
  () => `${window.location.origin}/api/data/v1/integrations/feishu/webhook`,
);

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
    if (config.api_type === 'feishu') {
      const extra = (config.extra ?? {}) as Record<string, unknown>;
      feishuFields.value = {
        app_id: stringOrEmpty(extra.app_id),
        app_secret: '',
        verification_token: stringOrEmpty(extra.verification_token),
        encrypt_key: stringOrEmpty(extra.encrypt_key),
      };
    } else {
      feishuFields.value = emptyFeishuFields();
    }
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

function emptyFeishuFields(): FeishuFields {
  return { app_id: '', app_secret: '', verification_token: '', encrypt_key: '' };
}

function stringOrEmpty(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function submit(): void {
  if (isFeishu.value) {
    const extra: Record<string, unknown> = {
      app_id: feishuFields.value.app_id.trim(),
      verification_token: feishuFields.value.verification_token.trim(),
      encrypt_key: feishuFields.value.encrypt_key.trim(),
    };
    emit('submit', {
      ...form.value,
      api_key: feishuFields.value.app_secret.trim() || null,
      extra,
    });
    return;
  }
  emit('submit', { ...form.value });
}

async function copyWebhookUrl(): Promise<void> {
  try {
    await navigator.clipboard?.writeText(webhookUrl.value);
  } catch {
    // 剪贴板 API 在非 HTTPS / 老浏览器会失败；用户可手动选择复制。
  }
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
      <el-form-item v-if="!isFeishu" label="模型">
        <el-input v-model="form.model" placeholder="如 deepseek-chat" />
      </el-form-item>
      <template v-if="isFeishu">
        <el-form-item label="App ID">
          <el-input v-model="feishuFields.app_id" placeholder="飞书应用 App ID（cli_开头）" />
        </el-form-item>
        <el-form-item label="App Secret">
          <el-input
            v-model="feishuFields.app_secret"
            type="password"
            show-password
            :placeholder="
              config.api_key_hint
                ? `当前 ${config.api_key_hint}，不改请留空`
                : '飞书开放平台 → 应用凭证 → App Secret'
            "
          />
        </el-form-item>
        <el-form-item label="Verification Token">
          <el-input
            v-model="feishuFields.verification_token"
            placeholder="飞书事件订阅页的 Verification Token"
          />
        </el-form-item>
        <el-form-item label="Encrypt Key">
          <el-input
            v-model="feishuFields.encrypt_key"
            type="password"
            show-password
            placeholder="飞书事件订阅页设置的 Encrypt Key（可选，留空表示不加密）"
          />
        </el-form-item>
        <el-form-item label="Webhook URL">
          <el-input :model-value="webhookUrl" readonly>
            <template #append>
              <el-button type="primary" @click="copyWebhookUrl"> 复制 </el-button>
            </template>
          </el-input>
          <div class="form-item-hint">
            把这个 URL 填到飞书开放平台 → 事件订阅 → 请求地址；服务器要有公网 HTTPS 才能通过校验。
          </div>
        </el-form-item>
      </template>
      <el-form-item v-else label="API Key">
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
      <el-form-item v-if="!isFeishu" label="重试次数">
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

<style scoped>
.form-item-hint {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.5;
}
</style>
