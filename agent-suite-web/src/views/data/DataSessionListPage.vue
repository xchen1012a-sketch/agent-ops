<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { dataQueryClient } from '@api/data-query';
import AgentChatLanding from '@components/chat/AgentChatLanding.vue';
import AsyncState from '@components/ui/AsyncState.vue';
import { useToastStore } from '@stores/toast';
import { createConversationTitle } from '@lib/conversation-title';
import { createErrorState, createLoadingState, createSuccessState } from '@lib/request-state';
import type { DataThread, DataThreadListData } from '@/types/data-query';
import type { RequestState } from '@/types/request-state';

const router = useRouter();
const toast = useToastStore();
const limit = 6;

const state = ref<RequestState<DataThreadListData>>({
  status: 'idle',
  data: null,
  error: null,
  updatedAt: null,
});
const firstQuestion = ref('');
const creating = ref(false);
const suggestions = [
  { label: '门店销售排行', prompt: '本周各门店销售额 Top 10 是哪些？' },
  { label: '客户增长趋势', prompt: '最近 30 天新增客户趋势如何？' },
  { label: '库存周转分析', prompt: '哪些商品库存周转较慢？' },
] as const;

async function loadThreads(): Promise<void> {
  state.value = createLoadingState();
  try {
    const response = await dataQueryClient.listThreads({ limit, offset: 0 });
    state.value = createSuccessState(response.data, {
      isEmpty: (data) => data.items.length === 0,
    });
  } catch (error) {
    state.value = createErrorState(normalizeRequestError(error));
  }
}

async function createThread(): Promise<void> {
  const question = firstQuestion.value.trim();
  if (!question) return;

  creating.value = true;
  try {
    const response = await dataQueryClient.createThread({
      title: createConversationTitle(question, '问数对话'),
    });
    toast.success('已开始');
    await router.push({
      name: 'data-session-detail',
      params: { id: response.data.thread_id },
      query: { q: question },
    });
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '创建失败，请重试');
  } finally {
    creating.value = false;
  }
}

async function openThread(thread: DataThread): Promise<void> {
  await router.push({ name: 'data-session-detail', params: { id: thread.thread_id } });
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function normalizeRequestError(error: unknown): Error | string {
  return error instanceof Error ? error : String(error ?? '加载失败');
}

onMounted(() => {
  void loadThreads();
});
</script>

<template>
  <AgentChatLanding
    v-model="firstQuestion"
    agent-name="智能问数"
    title="今天想了解哪些数据？"
    description="直接用日常语言提问，我会完成安全查询并整理趋势、排行和结论。"
    icon="DataAnalysis"
    tone="data"
    placeholder="向数据助手提问"
    hint="无需 SQL，Enter 发送"
    :suggestions="suggestions"
    :submitting="creating"
    @submit="createThread"
  >
    <template #after>
      <section class="data-chat-recents" aria-label="最近对话">
        <div class="data-chat-recents__header">
          <h2>最近对话</h2>
          <el-button text size="small" :loading="state.status === 'loading'" @click="loadThreads">
            刷新
          </el-button>
        </div>
        <AsyncState
          :state="state"
          loading-message="加载中…"
          empty-title="暂无对话"
          empty-description="发送第一条问题后会显示在这里。"
          empty-action-text=""
          @retry="loadThreads"
        >
          <template #default="{ data }">
            <div class="data-chat-recents__list">
              <button
                v-for="thread in data?.items ?? []"
                :key="thread.thread_id"
                type="button"
                @click="openThread(thread)"
              >
                <span>
                  <strong>{{ thread.title || '未命名对话' }}</strong>
                  <small>{{ formatDate(thread.updated_at) }}</small>
                </span>
                <el-tag size="small" effect="plain">{{ thread.status }}</el-tag>
              </button>
            </div>
          </template>
        </AsyncState>
      </section>
    </template>
  </AgentChatLanding>
</template>

<style scoped>
.data-chat-recents {
  display: grid;
  gap: var(--space-3);
  padding-top: var(--space-2);
}

.data-chat-recents__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.data-chat-recents__header h2 {
  font-size: var(--text-sm);
  font-weight: 700;
}

.data-chat-recents__list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
}

.data-chat-recents__list button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-width: 0;
  padding: var(--space-3) var(--space-4);
  color: var(--color-text);
  text-align: left;
  background: color-mix(in oklch, var(--color-surface) 78%, transparent);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.data-chat-recents__list button:hover {
  border-color: var(--color-data);
}

.data-chat-recents__list button > span {
  display: grid;
  gap: var(--space-1);
  min-width: 0;
}

.data-chat-recents__list strong,
.data-chat-recents__list small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-chat-recents__list small {
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

@media (max-width: 767px) {
  .data-chat-recents__list {
    grid-template-columns: 1fr;
  }
}
</style>
