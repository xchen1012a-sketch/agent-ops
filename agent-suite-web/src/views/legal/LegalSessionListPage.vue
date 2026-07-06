<script setup lang="ts">
import { ref } from 'vue';
import { ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';

import { legalClient } from '@api/legal';
import AgentChatLanding from '@components/chat/AgentChatLanding.vue';
import AsyncState from '@components/ui/AsyncState.vue';
import { useToastStore } from '@stores/toast';
import { createConversationTitle } from '@lib/conversation-title';
import {
  createErrorState,
  createLoadingState,
  createSuccessState,
  toRequestError,
} from '@lib/request-state';
import type { LegalSession, LegalSessionListData } from '@/types/legal';
import type { RequestState } from '@/types/request-state';

const router = useRouter();
const toast = useToastStore();

const firstQuestion = ref('');
const submitting = ref(false);
const sessions = ref<RequestState<LegalSessionListData>>({
  status: 'idle',
  data: null,
  error: null,
  updatedAt: null,
});
const suggestions = [
  { label: '拖欠工资怎么办', prompt: '公司拖欠工资，我该怎么处理？' },
  { label: '押金不退怎么办', prompt: '租房押金不退，可以怎么维权？' },
  { label: '审查合同条款', prompt: '合同里这条违约责任是否合理？' },
] as const;

async function createSession(): Promise<void> {
  const question = firstQuestion.value.trim();
  if (!question) return;

  submitting.value = true;
  try {
    const response = await legalClient.createSession({
      category_code: 'labor',
      title: createConversationTitle(question, '法律咨询'),
    });
    toast.success('已开始');
    await router.push({
      name: 'legal-session-detail',
      params: { id: response.data.public_id },
      query: { q: question },
    });
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '创建失败，请重试');
  } finally {
    submitting.value = false;
  }
}

async function loadSessions(): Promise<void> {
  sessions.value = createLoadingState();
  try {
    const response = await legalClient.listSessions({ limit: 8, offset: 0 });
    sessions.value = createSuccessState(response.data, {
      isEmpty: (data) => data.items.length === 0,
    });
  } catch (error) {
    sessions.value = createErrorState(toRequestError(error));
  }
}

async function openSession(session: LegalSession): Promise<void> {
  await router.push({ name: 'legal-session-detail', params: { id: session.public_id } });
}

async function renameSession(session: LegalSession): Promise<void> {
  let title: string;
  try {
    const result = await ElMessageBox.prompt('给这次咨询起个名字', '重命名', {
      inputValue: session.title ?? '',
      inputPlaceholder: '例如：劳动合同调岗',
      inputValidator: (value: string) => value.trim().length > 0 || '名称不能为空',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    });
    title = result.value.trim();
  } catch {
    return; // cancelled
  }

  try {
    await legalClient.renameSession(session.public_id, title);
    toast.success('已重命名');
    await loadSessions();
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '重命名失败，请重试');
  }
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

loadSessions();
</script>

<template>
  <AgentChatLanding
    v-model="firstQuestion"
    agent-name="法律助手"
    title="今天想咨询什么法律问题？"
    description="描述事实和诉求，我会先拆解风险，再提供有依据的处理建议。"
    icon="ChatDotRound"
    tone="legal"
    placeholder="向法律助手提问"
    hint="Enter 发送，Shift + Enter 换行"
    :suggestions="suggestions"
    :submitting="submitting"
    @submit="createSession"
  >
    <template #after>
      <section class="legal-chat-recents" aria-label="最近咨询">
        <div class="legal-chat-recents__header">
          <h2>最近咨询</h2>
          <el-button
            text
            size="small"
            :loading="sessions.status === 'loading'"
            @click="loadSessions"
          >
            刷新
          </el-button>
        </div>
        <AsyncState
          :state="sessions"
          loading-message="加载中…"
          empty-title="暂无咨询"
          empty-description="发送第一条问题后会显示在这里。"
          empty-action-text=""
          @retry="loadSessions"
        >
          <template #default="{ data }">
            <div class="legal-chat-recents__list">
              <div
                v-for="session in data?.items ?? []"
                :key="session.public_id"
                class="legal-chat-recents__item"
              >
                <button
                  type="button"
                  class="legal-chat-recents__open"
                  @click="openSession(session)"
                >
                  <strong>{{ session.title || '未命名咨询' }}</strong>
                  <small v-if="session.last_message_at">
                    {{ formatDate(session.last_message_at) }}
                  </small>
                </button>
                <el-button
                  text
                  size="small"
                  class="legal-chat-recents__rename"
                  @click.stop="renameSession(session)"
                >
                  重命名
                </el-button>
              </div>
            </div>
          </template>
        </AsyncState>
      </section>
    </template>
  </AgentChatLanding>
</template>

<style scoped>
.legal-chat-recents {
  display: grid;
  gap: var(--space-3);
  padding-top: var(--space-2);
}

.legal-chat-recents__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.legal-chat-recents__header h2 {
  font-size: var(--text-sm);
  font-weight: 700;
}

.legal-chat-recents__list {
  display: grid;
  gap: var(--space-2);
}

.legal-chat-recents__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: color-mix(in oklch, var(--color-surface) 78%, transparent);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: border-color var(--duration-fast) var(--ease-in-out);
}

.legal-chat-recents__item:hover {
  border-color: var(--color-legal);
}

.legal-chat-recents__open {
  display: flex;
  flex: 1 1 auto;
  align-items: baseline;
  gap: var(--space-3);
  min-width: 0;
  padding: 0;
  color: var(--color-text);
  text-align: left;
  background: none;
  border: 0;
  cursor: pointer;
}

.legal-chat-recents__open strong {
  overflow: hidden;
  font-size: var(--text-sm);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legal-chat-recents__open small {
  flex: 0 0 auto;
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.legal-chat-recents__rename {
  flex: 0 0 auto;
}
</style>
