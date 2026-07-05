<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { dataQueryClient } from '@api/data-query';
import ChatComposer from '@components/chat/ChatComposer.vue';
import AsyncState from '@components/ui/AsyncState.vue';
import AppIcon from '@components/ui/AppIcon.vue';
import SSEStatusIndicator from '@components/ui/SSEStatusIndicator.vue';
import { useToastStore } from '@stores/toast';
import { createConversationTitle } from '@lib/conversation-title';
import { createErrorState, createLoadingState, createSuccessState } from '@lib/request-state';
import type { DataRunDetail, DataSseContractEvent, DataThread } from '@/types/data-query';
import type { RequestState } from '@/types/request-state';
import type { AgentStreamClient } from '@lib/sse-client';
import type { AgentStreamEvent, StreamState } from '@/types/sse';

const route = useRoute();
const router = useRouter();
const toast = useToastStore();

const threadId = computed(() => String(route.params.id));
const threadState = ref<RequestState<DataThread>>({
  status: 'idle',
  data: null,
  error: null,
  updatedAt: null,
});
const question = ref(typeof route.query.q === 'string' ? route.query.q : '');
const currentQuestion = ref('');
const submitting = ref(false);
const runDetail = ref<DataRunDetail | null>(null);
const streamState = ref<StreamState>('idle');
const streamEvents = ref<DataSseContractEvent[]>([]);
let streamClient: AgentStreamClient | null = null;

const generatedThreadTitle = computed(() =>
  createConversationTitle(currentQuestion.value || question.value, '新的问数对话'),
);
const canControlRun = computed(() => Boolean(runDetail.value?.run_id));
const runStatusType = computed(() => {
  switch (runDetail.value?.status) {
    case 'success':
      return 'success';
    case 'failed':
      return 'danger';
    case 'canceled':
      return 'warning';
    case 'running':
    case 'retrying':
      return 'primary';
    default:
      return 'info';
  }
});

async function loadThread(): Promise<void> {
  threadState.value = createLoadingState();
  try {
    const response = await dataQueryClient.getThread(threadId.value);
    threadState.value = createSuccessState(response.data);
  } catch (error) {
    threadState.value = createErrorState(normalizeRequestError(error));
  }
}

async function submitQuestion(): Promise<void> {
  const trimmed = question.value.trim();
  if (!trimmed) return;

  submitting.value = true;
  stopStream();
  streamEvents.value = [];
  runDetail.value = null;
  try {
    const response = await dataQueryClient.createRun(threadId.value, {
      question: trimmed,
      channel: 'web',
      locale: navigator.language || 'zh-CN',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
    currentQuestion.value = response.data.question;
    question.value = '';
    await refreshRun(response.data.run_id);
    startStream(response.data.run_id);
    toast.success('问题已提交到智能问数 Agent');
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '提交问数问题失败');
  } finally {
    submitting.value = false;
  }
}

async function refreshRun(runId = runDetail.value?.run_id): Promise<void> {
  if (!runId) return;
  try {
    const response = await dataQueryClient.getRun(runId);
    runDetail.value = response.data;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载运行状态失败');
  }
}

async function cancelRun(): Promise<void> {
  if (!runDetail.value) return;
  try {
    const response = await dataQueryClient.cancelRun(runDetail.value.run_id);
    runDetail.value = response.data;
    stopStream();
    toast.info('运行已取消');
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '取消运行失败');
  }
}

async function retryRun(): Promise<void> {
  if (!runDetail.value) return;
  try {
    const response = await dataQueryClient.retryRun(runDetail.value.run_id);
    runDetail.value = response.data;
    streamEvents.value = [];
    startStream(response.data.run_id);
    toast.success('运行已重试');
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '重试运行失败');
  }
}

function startStream(runId: string): void {
  stopStream();
  streamClient = dataQueryClient.createRunStream({
    runId,
    onEvent: handleStreamEvent,
    onStateChange: (state) => {
      streamState.value = state;
    },
  });
  streamClient.start();
}

function stopStream(): void {
  streamClient?.stop();
  streamClient = null;
  if (streamState.value !== 'idle') {
    streamState.value = 'closed';
  }
}

async function copyText(content: string): Promise<void> {
  if (typeof navigator === 'undefined' || !navigator.clipboard) return;
  await navigator.clipboard.writeText(content);
  toast.success('已复制');
}

function handleStreamEvent(event: AgentStreamEvent): void {
  streamEvents.value.push({
    event: event.event ?? 'message',
    payload: (event.payload ?? {}) as Record<string, unknown>,
    received_at: event.timestamp,
  });

  if (event.event === 'run.completed' || event.event === 'run.failed') {
    void refreshRun(event.run_id);
  }
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value));
}

function formatRunThoughtLabel(detail: DataRunDetail): string {
  if (detail.status === 'running' || detail.status === 'retrying') {
    return 'Thinking';
  }
  if (detail.started_at && detail.finished_at) {
    const elapsedMs =
      new Date(detail.finished_at).getTime() - new Date(detail.started_at).getTime();
    if (Number.isFinite(elapsedMs) && elapsedMs > 0) {
      return `Thought for ${Math.max(1, Math.round(elapsedMs / 1000))}s`;
    }
  }
  return 'Thought through answer';
}

function normalizeRequestError(error: unknown): Error | string {
  return error instanceof Error ? error : String(error ?? '加载失败');
}

onMounted(() => {
  void (async () => {
    await loadThread();
    if (question.value.trim()) {
      await submitQuestion();
      await router.replace({
        name: 'data-session-detail',
        params: { id: threadId.value },
      });
    }
  })();
});

onBeforeUnmount(() => {
  stopStream();
});
</script>

<template>
  <div class="data-chat-page">
    <AsyncState
      :state="threadState"
      loading-message="加载中…"
      empty-title="会话不存在"
      @retry="loadThread"
    >
      <template #default="{ data }">
        <header class="data-chat-page__topbar" aria-labelledby="data-session-title">
          <div>
            <p class="data-chat-page__eyebrow">智能问数</p>
            <h1 id="data-session-title">{{ data?.title || generatedThreadTitle }}</h1>
          </div>
          <SSEStatusIndicator :state="streamState" />
        </header>

        <main class="data-chat-page__conversation" aria-label="问数对话">
          <EmptyState
            v-if="!currentQuestion && !runDetail && streamEvents.length === 0"
            title="直接问数据"
            description="把问题写在下方。"
            icon="DataAnalysis"
          />

          <div v-else class="data-chat-page__messages">
            <article v-if="currentQuestion" class="data-message data-message--user">
              <div class="data-message__avatar" aria-hidden="true">我</div>
              <div class="data-message__body">
                <div class="data-message__meta"><strong>我</strong></div>
                <p>{{ currentQuestion }}</p>
              </div>
            </article>

            <article v-if="runDetail" class="data-message data-message--assistant">
              <div class="data-message__avatar" aria-hidden="true">AI</div>
              <div class="data-message__body">
                <div class="data-message__meta">
                  <strong>{{ formatRunThoughtLabel(runDetail) }}</strong>
                  <el-tag :type="runStatusType" effect="light">{{ runDetail.status }}</el-tag>
                </div>

                <p v-if="runDetail.status === 'success'">分析已完成。</p>
                <p v-else-if="runDetail.status === 'failed'" class="data-message__error">
                  {{ runDetail.error_message || '这次分析失败了，可以重试。' }}
                </p>
                <p v-else-if="runDetail.status === 'canceled'">已取消。</p>
                <p v-else>正在分析…</p>

                <div class="data-message__actions">
                  <el-button text circle aria-label="复制问题" @click="copyText(currentQuestion)">
                    <AppIcon name="Copy" />
                  </el-button>
                  <el-button
                    text
                    circle
                    aria-label="刷新运行"
                    :disabled="!canControlRun"
                    @click="refreshRun()"
                  >
                    <AppIcon name="Refresh" />
                  </el-button>
                  <el-button
                    text
                    circle
                    aria-label="取消运行"
                    :disabled="!canControlRun"
                    @click="cancelRun"
                  >
                    <AppIcon name="CircleClose" />
                  </el-button>
                  <el-button
                    text
                    circle
                    aria-label="重试运行"
                    :disabled="!canControlRun"
                    @click="retryRun"
                  >
                    <AppIcon name="Play" />
                  </el-button>
                </div>

                <details class="data-message__details">
                  <summary>运行细节</summary>
                  <dl>
                    <div>
                      <dt>Run ID</dt>
                      <dd>{{ runDetail.run_id }}</dd>
                    </div>
                    <div>
                      <dt>创建</dt>
                      <dd>{{ formatDate(runDetail.created_at) }}</dd>
                    </div>
                    <div>
                      <dt>开始</dt>
                      <dd>{{ formatDate(runDetail.started_at) }}</dd>
                    </div>
                    <div>
                      <dt>结束</dt>
                      <dd>{{ formatDate(runDetail.finished_at) }}</dd>
                    </div>
                    <div v-if="runDetail.error_code">
                      <dt>错误</dt>
                      <dd>{{ runDetail.error_code }}</dd>
                    </div>
                  </dl>
                </details>

                <details v-if="streamEvents.length" class="data-message__details">
                  <summary>事件记录</summary>
                  <ol class="data-message__events">
                    <li v-for="(item, index) in streamEvents" :key="`${item.event}-${index}`">
                      <strong>{{ item.event }}</strong>
                      <span>{{ formatDate(item.received_at) }}</span>
                    </li>
                  </ol>
                </details>
              </div>
            </article>
          </div>
        </main>

        <footer class="data-chat-page__composer-shell" aria-label="发送问数问题">
          <ChatComposer
            v-model="question"
            tone="data"
            placeholder="继续问数据…"
            hint="Enter 发送，Shift + Enter 换行"
            input-label="智能问数问题"
            :submitting="submitting"
            @submit="submitQuestion"
          />
        </footer>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.data-chat-page {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: var(--space-4);
  max-width: 980px;
  min-height: calc(100vh - 180px);
  margin: 0 auto;
}

.data-chat-page__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 var(--space-1) var(--space-5);
}

.data-chat-page__eyebrow {
  margin-bottom: var(--space-1);
  color: var(--color-data);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.data-chat-page__topbar h1 {
  max-width: 720px;
  overflow-wrap: anywhere;
  font-size: var(--text-xl);
  font-weight: 650;
}

.data-chat-page__conversation {
  min-height: 54vh;
  padding-bottom: var(--space-4);
}

.data-chat-page__messages {
  display: grid;
  gap: var(--space-8);
}

.data-message {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: var(--space-3);
  align-items: start;
}

.data-message--user {
  grid-template-columns: minmax(0, 1fr);
  max-width: min(72%, 520px);
  margin-left: auto;
}

.data-message--user .data-message__avatar {
  display: none;
}

.data-message--user .data-message__body {
  grid-column: 1;
  grid-row: 1;
  justify-self: end;
  color: var(--color-text);
  background: var(--color-surface-muted);
  border-color: transparent;
  border-radius: 14px;
  box-shadow: none;
}

.data-message--assistant .data-message__avatar {
  align-self: end;
  color: var(--color-primary);
  background: transparent;
  font-size: 0;
}

.data-message__avatar {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-pill);
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  font-size: var(--text-xs);
  font-weight: 700;
}

.data-message--assistant .data-message__avatar::before {
  width: 24px;
  height: 24px;
  background: repeating-conic-gradient(
    from 0deg,
    currentColor 0deg 10deg,
    transparent 10deg 22.5deg
  );
  border-radius: var(--radius-pill);
  content: '';
}

.data-message__body {
  max-width: 100%;
  padding: var(--space-4);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  overflow-wrap: anywhere;
}

.data-message--assistant .data-message__body {
  padding: 0 0 var(--space-2);
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.data-message__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.data-message--user .data-message__meta {
  display: none;
}

.data-message--assistant .data-message__meta {
  justify-content: flex-start;
  color: var(--color-text-subtle);
}

.data-message__error {
  color: var(--color-danger);
}

.data-message__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin-top: var(--space-4);
}

.data-message__actions .el-button {
  width: 28px;
  height: 28px;
  margin: 0;
  color: var(--color-text-subtle);
}

.data-message__actions .el-button:hover {
  color: var(--color-text);
  background: var(--color-surface-muted);
}

.data-message__details {
  margin-top: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.data-message__details summary {
  cursor: pointer;
}

.data-message__details dl,
.data-message__events {
  display: grid;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.data-message__details dl div {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: var(--space-2);
}

.data-message__details dd {
  overflow-wrap: anywhere;
}

.data-message__events {
  padding-left: var(--space-4);
}

.data-message__events li {
  overflow-wrap: anywhere;
}

.data-message__events span {
  margin-left: var(--space-2);
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}

.data-chat-page__composer-shell {
  position: sticky;
  bottom: var(--space-4);
  z-index: var(--z-sticky);
  padding-top: var(--space-4);
  background: linear-gradient(180deg, transparent, var(--color-bg) 34%);
}

@media (max-width: 767px) {
  .data-chat-page__topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .data-message,
  .data-message--user {
    grid-template-columns: 32px minmax(0, 1fr);
    max-width: 100%;
  }

  .data-message--user .data-message__avatar {
    display: none;
  }

  .data-message--user .data-message__body {
    grid-column: 1 / -1;
  }

  .data-message__avatar {
    width: 32px;
    height: 32px;
  }
}
</style>
