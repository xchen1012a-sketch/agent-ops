<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import ApiConfigEditor from '@components/admin/ApiConfigEditor.vue';
import {
  buildDefaultAgentApiConfigs,
  listAgentApiConfigs,
  updateAgentApiConfig,
} from '@api/admin-api-config';
import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';
import type { AgentApiConfigUpdate, AgentApiConfigView, AgentName } from '@/types/admin-api-config';

const toastStore = useToastStore();
const authStore = useAuthStore();

const agentCards: { agent: AgentName; label: string; description: string }[] = [
  {
    agent: 'legal',
    label: '法律咨询 Agent',
    description: 'DeepSeek 必需；Embedding / 向量库 / Reranker 用于 RAG；OCR 仅扫描材料需要',
  },
  {
    agent: 'recruitment',
    label: '智能招聘 Agent',
    description: 'DeepSeek 必需；OCR 仅扫描简历或 JD 需要',
  },
  {
    agent: 'data',
    label: '智能问数 Agent',
    description: 'DeepSeek 必需；MCP 用于真查询；飞书仅消息入口需要',
  },
];

const activeAgent = ref<AgentName>('legal');
const configsByAgent = ref<Record<AgentName, AgentApiConfigView[]>>({
  legal: [],
  recruitment: [],
  data: [],
});
const loadingAgent = ref<Record<AgentName, boolean>>({
  legal: false,
  recruitment: false,
  data: false,
});
const loadErrors = ref<Record<AgentName, string | null>>({
  legal: null,
  recruitment: null,
  data: null,
});
const activeAgentCard = computed(
  () => agentCards.find((card) => card.agent === activeAgent.value) ?? agentCards[0],
);
const card = activeAgentCard;
const activeConfigs = computed(() => configsByAgent.value[activeAgent.value]);
const activeLoading = computed(() => loadingAgent.value[activeAgent.value]);
const activeLoadError = computed(() => loadErrors.value[activeAgent.value]);

const editorVisible = ref(false);
const editorAgent = ref<AgentName | null>(null);
const editorConfig = ref<AgentApiConfigView | null>(null);
const editorSaving = ref(false);

async function loadAgentConfigs(agent: AgentName): Promise<void> {
  loadingAgent.value[agent] = true;
  loadErrors.value[agent] = null;
  try {
    configsByAgent.value[agent] = await listAgentApiConfigs(agent);
  } catch {
    configsByAgent.value[agent] = buildDefaultAgentApiConfigs(
      agent,
      authStore.profile?.public_id ?? '',
    );
    loadErrors.value[agent] =
      '当前后端配置接口暂不可用，已显示默认依赖项；可以先编辑，保存需要后端恢复。';
  } finally {
    loadingAgent.value[agent] = false;
  }
}

async function loadAll(): Promise<void> {
  await Promise.all(agentCards.map((card) => loadAgentConfigs(card.agent)));
}

function selectAgent(agent: AgentName): void {
  activeAgent.value = agent;
}

// CONFIG-200: only the deepseek dependency drives real-vs-mock streaming; a row
// counts as "真实" once it is enabled and has a stored key hint.
function effectiveSource(row: AgentApiConfigView): '真实' | '模拟' | '—' {
  if (row.api_type !== 'deepseek') return '—';
  return row.enabled && row.api_key_hint ? '真实' : '模拟';
}

function openEditorFromRow(agent: AgentName, row: unknown): void {
  editorAgent.value = agent;
  editorConfig.value = row as AgentApiConfigView;
  editorVisible.value = true;
}

async function saveConfig(payload: AgentApiConfigUpdate): Promise<void> {
  if (editorAgent.value === null || editorConfig.value === null) return;
  const agent = editorAgent.value;
  const apiType = editorConfig.value.api_type;
  editorSaving.value = true;
  try {
    const updated = await updateAgentApiConfig(agent, apiType, payload);
    configsByAgent.value[agent] = configsByAgent.value[agent].map((item) =>
      item.api_type === updated.api_type ? updated : item,
    );
    loadErrors.value[agent] = null;
    toastStore.success('已保存到当前账号的 API 配置', '配置已更新');
    editorVisible.value = false;
  } catch {
    // 全局 Toast 已由 http-client 错误处理兜底
  } finally {
    editorSaving.value = false;
  }
}

onMounted(() => {
  void loadAll();
});
</script>

<template>
  <div class="api-config-page">
    <section class="api-config-page__hero">
      <div>
        <p class="api-config-page__eyebrow">配置中心</p>
        <h1>外部 API 配置</h1>
        <p class="api-config-page__description">
          管理当前账号在三个助手中使用的外部 API。密钥加密存储，仅显示遮挡值；其他账号不可见。
        </p>
      </div>
      <el-button
        :loading="loadingAgent.legal || loadingAgent.recruitment || loadingAgent.data"
        @click="loadAll"
      >
        刷新
      </el-button>
    </section>

    <section class="api-config-page__panel" aria-label="Agent API 配置">
      <div class="api-config-page__agent-switch" role="tablist" aria-label="选择 Agent">
        <button
          v-for="agentCard in agentCards"
          :key="agentCard.agent"
          type="button"
          class="api-config-page__agent-tab"
          :class="{ 'is-active': activeAgent === agentCard.agent }"
          role="tab"
          :aria-selected="activeAgent === agentCard.agent"
          @click="selectAgent(agentCard.agent)"
        >
          {{ agentCard.label }}
        </button>
      </div>

      <div :key="activeAgent" class="api-config-page__tab-body" role="tabpanel">
        <div class="api-config-page__tab-summary">
          <p>{{ activeAgentCard.description }}</p>
          <span>{{ configsByAgent[card.agent].length }} 项依赖</span>
        </div>
        <p class="api-config-page__note">
          DeepSeek 启用并填入 Key 后，思考与回答会切换为真实模型；未配置时使用内置模拟。同一
          Key 需在每个 Agent 各配置一次。
        </p>
        <el-alert
          v-if="activeLoadError"
          class="api-config-page__alert"
          type="warning"
          show-icon
          :closable="false"
          :title="activeLoadError"
        />
        <el-table
          v-loading="activeLoading"
          :data="activeConfigs"
          row-key="api_type"
          empty-text="尚未配置"
        >
          <el-table-column prop="display_name" label="API" min-width="140" />
          <el-table-column label="Base URL" min-width="200">
            <template #default="{ row }">
              <code>{{ row.base_url || '—' }}</code>
            </template>
          </el-table-column>
          <el-table-column label="模型" min-width="120">
            <template #default="{ row }">{{ row.model || '—' }}</template>
          </el-table-column>
          <el-table-column label="Key" min-width="130">
            <template #default="{ row }">
              <code>{{ row.api_key_hint || '未设置' }}</code>
            </template>
          </el-table-column>
          <el-table-column label="超时/重试" width="110">
            <template #default="{ row }">
              {{ row.timeout_seconds ?? '—' }}s / {{ row.max_retries ?? '—' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" effect="light">
                {{ row.enabled ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="生效来源" width="100">
            <template #default="{ row }">
              <el-tag
                v-if="effectiveSource(row as AgentApiConfigView) !== '—'"
                :type="effectiveSource(row as AgentApiConfigView) === '真实' ? 'success' : 'info'"
                effect="plain"
              >
                {{ effectiveSource(row as AgentApiConfigView) }}
              </el-tag>
              <span v-else>—</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                link
                type="primary"
                @click="openEditorFromRow(card.agent, row)"
              >
                编辑
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <ApiConfigEditor
      v-model="editorVisible"
      :config="editorConfig"
      :saving="editorSaving"
      @submit="saveConfig"
    />
  </div>
</template>

<style scoped>
.api-config-page {
  width: 100%;
  max-width: 1080px;
  margin: var(--space-4) 0;
  padding: 0 var(--space-6) var(--space-8);
}

.api-config-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  margin-bottom: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.api-config-page__hero h1 {
  font-size: var(--text-2xl);
  line-height: var(--line-tight);
}

.api-config-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.api-config-page__description {
  max-width: 760px;
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.api-config-page__panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.api-config-page__agent-switch {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2);
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
}

.api-config-page__agent-tab {
  min-width: 148px;
  min-height: 38px;
  padding: 0 var(--space-4);
  border: 1px solid transparent;
  background: transparent;
  border-radius: 6px;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-in-out),
    border-color var(--duration-fast) var(--ease-in-out),
    color var(--duration-fast) var(--ease-in-out),
    box-shadow var(--duration-fast) var(--ease-in-out);
}

.api-config-page__agent-tab:hover {
  color: var(--color-text);
  background: color-mix(in oklch, var(--color-surface), transparent 20%);
}

.api-config-page__agent-tab.is-active {
  background: var(--color-surface);
  border-color: color-mix(in oklch, var(--color-primary), var(--color-border) 55%);
  color: var(--color-primary);
  box-shadow: var(--shadow-card);
}

.api-config-page__tab-body {
  padding: var(--space-4);
}

.api-config-page__tab-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.api-config-page__tab-summary p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.api-config-page__tab-summary span {
  flex: 0 0 auto;
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.api-config-page__note {
  margin: 0 0 var(--space-3);
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
  line-height: var(--line-relaxed);
}

.api-config-page__alert {
  margin-bottom: var(--space-3);
}

code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

:deep(.el-table) {
  --el-table-header-bg-color: var(--color-surface-muted);
  --el-table-border-color: var(--color-border);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

:deep(.el-table th.el-table__cell) {
  color: var(--color-text-muted);
  font-weight: 700;
}

:deep(.el-table__inner-wrapper::before) {
  display: none;
}

@media (max-width: 767px) {
  .api-config-page {
    margin-top: var(--space-4);
    padding-inline: var(--space-3);
  }

  .api-config-page__hero {
    flex-direction: column;
    padding: var(--space-4);
  }

  .api-config-page__agent-switch,
  .api-config-page__tab-summary {
    flex-direction: column;
    align-items: stretch;
  }

  .api-config-page__agent-tab {
    width: 100%;
  }
}
</style>
