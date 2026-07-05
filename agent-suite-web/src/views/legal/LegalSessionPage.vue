<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { legalClient } from '@api/legal';
import ChatComposer from '@components/chat/ChatComposer.vue';
import EmptyState from '@components/ui/EmptyState.vue';
import AppIcon from '@components/ui/AppIcon.vue';
import LoadingState from '@components/ui/LoadingState.vue';
import SafeMarkdown from '@components/ui/SafeMarkdown.vue';
import SSEStatusIndicator from '@components/ui/SSEStatusIndicator.vue';
import { useToastStore } from '@stores/toast';
import { createConversationTitle } from '@lib/conversation-title';
import type { AgentStreamClient } from '@lib/sse-client';
import type { AgentStreamEvent, StreamState } from '@/types/sse';
import type { LegalMessage, LegalQuestionAnswer } from '@/types/legal';

const route = useRoute();
const router = useRouter();
const toast = useToastStore();

const sessionPublicId = computed(() => String(route.params.id));
const messages = ref<LegalMessage[]>([]);
const currentAnswer = ref<LegalQuestionAnswer | null>(null);
const loadingMessages = ref(false);
const submitting = ref(false);
const question = ref(typeof route.query.q === 'string' ? route.query.q : '');
const pendingQuestion = ref('');
const streamingAnswer = ref('');
const streamState = ref<StreamState>('idle');
const thinkingStartedAt = ref<number | null>(null);
const thinkingElapsedSeconds = ref(0);
const feedbackDialogVisible = ref(false);
const reviewDialogVisible = ref(false);
const selectedMessage = ref<LegalMessage | null>(null);
const feedbackRating = ref(5);
const feedbackComment = ref('');
const reviewReason = ref('');
const secondarySubmitting = ref(false);
let streamClient: AgentStreamClient | null = null;
let thinkingTimer: number | null = null;

const liveThoughtLabel = computed(() =>
  streamingAnswer.value || currentAnswer.value
    ? `Thought for ${formatThoughtSeconds(thinkingElapsedSeconds.value)}`
    : 'Thinking',
);
const sessionTitle = computed(() => {
  const firstUserMessage = messages.value.find((message) => message.role === 'user');
  return createConversationTitle(
    pendingQuestion.value || question.value || firstUserMessage?.content,
    '新的法律咨询',
  );
});

async function loadMessages(): Promise<void> {
  loadingMessages.value = true;
  try {
    const response = await legalClient.listMessages(sessionPublicId.value, {
      limit: 50,
      offset: 0,
    });
    messages.value = response.data.items;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载失败');
  } finally {
    loadingMessages.value = false;
  }
}

async function submitQuestion(): Promise<void> {
  const normalized = question.value.trim();
  if (!normalized) return;

  submitting.value = true;
  stopStream();
  currentAnswer.value = null;
  pendingQuestion.value = normalized;
  streamingAnswer.value = '';
  startThinkingTimer();
  try {
    streamClient = legalClient.createQuestionStream({
      sessionPublicId: sessionPublicId.value,
      question: normalized,
      onEvent: handleStreamEvent,
      onStateChange: handleStreamStateChange,
    });
    streamClient.start();
  } catch (error) {
    submitting.value = false;
    toast.error(error instanceof Error ? error.message : '发送失败，请重试');
  }
}

function handleStreamStateChange(state: StreamState): void {
  streamState.value = state;
  if (state === 'error') {
    submitting.value = false;
    stopThinkingTimer();
    toast.error('流式连接中断，请重试');
  }
}

function handleStreamEvent(event: AgentStreamEvent): void {
  const payload = (event.payload ?? {}) as Record<string, unknown>;

  if (event.event === 'message.delta' && typeof payload.delta === 'string') {
    streamingAnswer.value += payload.delta;
    return;
  }

  if (event.event === 'completed') {
    const answer = payload as unknown as LegalQuestionAnswer;
    currentAnswer.value = answer;
    streamingAnswer.value = answer.answer || streamingAnswer.value;
    question.value = '';
    submitting.value = false;
    stopThinkingTimer();
    stopStream();
    void (async () => {
      await loadMessages();
      pendingQuestion.value = '';
      streamingAnswer.value = '';
      toast.success('已回复');
    })();
  }
}

function stopStream(): void {
  streamClient?.stop();
  streamClient = null;
  if (streamState.value !== 'idle') {
    streamState.value = 'closed';
  }
}

function startThinkingTimer(): void {
  stopThinkingTimer();
  thinkingStartedAt.value = Date.now();
  thinkingElapsedSeconds.value = 0;
  thinkingTimer = window.setInterval(() => {
    if (!thinkingStartedAt.value) return;
    thinkingElapsedSeconds.value = Math.max(
      1,
      Math.round((Date.now() - thinkingStartedAt.value) / 1000),
    );
  }, 250);
}

function stopThinkingTimer(): void {
  if (thinkingTimer !== null) {
    window.clearInterval(thinkingTimer);
    thinkingTimer = null;
  }
  if (thinkingStartedAt.value) {
    thinkingElapsedSeconds.value = Math.max(
      1,
      Math.round((Date.now() - thinkingStartedAt.value) / 1000),
    );
  }
}

function formatThoughtSeconds(seconds: number): string {
  return `${Math.max(1, seconds)}s`;
}

function assistantThoughtLabel(message: LegalMessage): string {
  if (currentAnswer.value?.answer_message.public_id === message.public_id) {
    return `Thought for ${formatThoughtSeconds(thinkingElapsedSeconds.value)}`;
  }
  return 'Thought through answer';
}

function messageTone(role: LegalMessage['role']): string {
  if (role === 'assistant') return 'assistant';
  if (role === 'system') return 'system';
  return 'user';
}

function openFeedbackDialog(message: LegalMessage): void {
  selectedMessage.value = message;
  feedbackRating.value = 5;
  feedbackComment.value = '';
  feedbackDialogVisible.value = true;
}

async function copyMessage(content: string): Promise<void> {
  if (typeof navigator === 'undefined' || !navigator.clipboard) return;
  await navigator.clipboard.writeText(content);
  toast.success('已复制');
}

function openReviewDialog(message: LegalMessage): void {
  selectedMessage.value = message;
  reviewReason.value = message.high_risk ? '需要人工确认' : '';
  reviewDialogVisible.value = true;
}

async function submitFeedback(): Promise<void> {
  if (!selectedMessage.value) return;
  secondarySubmitting.value = true;
  try {
    await legalClient.createFeedback(sessionPublicId.value, selectedMessage.value.public_id, {
      rating: feedbackRating.value,
      comment: feedbackComment.value.trim() || null,
    });
    toast.success('谢谢反馈');
    feedbackDialogVisible.value = false;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '提交失败，请重试');
  } finally {
    secondarySubmitting.value = false;
  }
}

async function submitHighRiskReview(): Promise<void> {
  if (!selectedMessage.value || !reviewReason.value.trim()) return;
  secondarySubmitting.value = true;
  try {
    await legalClient.createHighRiskReview(sessionPublicId.value, selectedMessage.value.public_id, {
      reason: reviewReason.value.trim(),
    });
    toast.success('已提交');
    reviewDialogVisible.value = false;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '提交失败，请重试');
  } finally {
    secondarySubmitting.value = false;
  }
}

onMounted(() => {
  void (async () => {
    await loadMessages();
    if (question.value.trim()) {
      await submitQuestion();
      await router.replace({
        name: 'legal-session-detail',
        params: { id: sessionPublicId.value },
      });
    }
  })();
});

onBeforeUnmount(() => {
  stopThinkingTimer();
  stopStream();
});
</script>

<template>
  <div class="legal-chat-page">
    <header class="legal-chat-page__topbar" aria-labelledby="legal-session-title">
      <div>
        <p class="legal-chat-page__eyebrow">法律助手</p>
        <h1 id="legal-session-title">{{ sessionTitle }}</h1>
      </div>
      <div class="legal-chat-page__tools">
        <SSEStatusIndicator v-if="streamState !== 'idle'" :state="streamState" />
        <el-button text :loading="loadingMessages" @click="loadMessages">刷新</el-button>
      </div>
    </header>

    <main class="legal-chat-page__conversation" aria-label="法律对话">
      <LoadingState v-if="loadingMessages" message="加载中…" />
      <EmptyState
        v-else-if="messages.length === 0 && !pendingQuestion"
        title="直接开始问"
        description="把问题写在下方。"
        icon="ChatDotRound"
      />
      <div v-else class="legal-chat-page__messages">
        <article
          v-for="message in messages"
          :key="message.public_id"
          class="legal-message"
          :class="`legal-message--${messageTone(message.role)}`"
        >
          <div class="legal-message__avatar" aria-hidden="true">
            {{ message.role === 'assistant' ? 'AI' : message.role === 'system' ? 'S' : '我' }}
          </div>

          <div class="legal-message__body">
            <div class="legal-message__meta">
              <strong>{{
                message.role === 'assistant'
                  ? assistantThoughtLabel(message)
                  : message.role === 'system'
                    ? '系统'
                    : '我'
              }}</strong>
              <el-tag v-if="message.high_risk" type="warning" effect="light">需确认</el-tag>
            </div>

            <div class="legal-message__content">
              <SafeMarkdown :source="message.content" />
            </div>

            <details v-if="message.citations?.length" class="legal-message__citations">
              <summary>查看依据</summary>
              <blockquote v-for="citation in message.citations" :key="citation.snippet">
                <strong>{{ citation.source ?? '资料' }}</strong>
                <span v-if="citation.section"> · {{ citation.section }}</span>
                <p>{{ citation.snippet }}</p>
              </blockquote>
            </details>

            <div v-if="message.role === 'assistant'" class="legal-message__actions">
              <el-button text circle aria-label="复制回答" @click="copyMessage(message.content)">
                <AppIcon name="Copy" />
              </el-button>
              <el-button text circle aria-label="朗读回答">
                <AppIcon name="Play" />
              </el-button>
              <el-button text circle aria-label="反馈回答" @click="openFeedbackDialog(message)">
                <AppIcon name="ThumbsUp" />
              </el-button>
              <el-button text circle aria-label="人工确认" @click="openReviewDialog(message)">
                <AppIcon name="ThumbsDown" />
              </el-button>
            </div>
          </div>
        </article>

        <article v-if="pendingQuestion" class="legal-message legal-message--user">
          <div class="legal-message__avatar" aria-hidden="true">我</div>
          <div class="legal-message__body">
            <div class="legal-message__meta"><strong>我</strong></div>
            <div class="legal-message__content">
              <SafeMarkdown :source="pendingQuestion" />
            </div>
          </div>
        </article>

        <article
          v-if="pendingQuestion || streamingAnswer"
          class="legal-message legal-message--assistant"
        >
          <div class="legal-message__avatar" aria-hidden="true">AI</div>
          <div class="legal-message__body">
            <div class="legal-message__meta">
              <strong>{{ liveThoughtLabel }}</strong>
            </div>
            <div class="legal-message__content">
              <SafeMarkdown :source="streamingAnswer || '正在生成…'" />
            </div>
          </div>
        </article>
      </div>
    </main>

    <footer class="legal-chat-page__composer-shell" aria-label="发送问题">
      <el-alert
        v-if="currentAnswer?.high_risk"
        class="legal-chat-page__risk"
        type="warning"
        :title="currentAnswer.risk_reason ?? '这类问题建议再做人工确认'"
        show-icon
        :closable="false"
      />
      <ChatComposer
        v-model="question"
        tone="legal"
        placeholder="继续提问…"
        hint="Enter 发送，Shift + Enter 换行"
        input-label="向法律助手提问"
        :submitting="submitting"
        @submit="submitQuestion"
      />
    </footer>

    <el-dialog v-model="feedbackDialogVisible" title="反馈" width="420px">
      <el-form label-position="top" @submit.prevent="submitFeedback">
        <el-form-item label="评分">
          <el-rate v-model="feedbackRating" :max="5" aria-label="评分" />
        </el-form-item>
        <el-form-item label="补充">
          <el-input
            v-model="feedbackComment"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="可不填"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="secondarySubmitting" @click="submitFeedback">
          提交
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewDialogVisible" title="人工确认" width="460px">
      <el-form label-position="top">
        <el-form-item label="原因" required>
          <el-input
            v-model="reviewReason"
            type="textarea"
            :rows="4"
            maxlength="200"
            show-word-limit
            placeholder="简单说明即可"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button
          type="warning"
          :loading="secondarySubmitting"
          :disabled="!reviewReason.trim()"
          @click="submitHighRiskReview"
        >
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.legal-chat-page {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: var(--space-4);
  max-width: 980px;
  min-height: calc(100vh - 180px);
  margin: 0 auto;
}

.legal-chat-page__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 var(--space-1);
}

.legal-chat-page__tools {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}

.legal-chat-page__eyebrow {
  margin-bottom: var(--space-1);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.legal-chat-page__topbar h1 {
  font-size: var(--text-xl);
  font-weight: 650;
}

.legal-chat-page__conversation {
  min-height: 54vh;
  padding-bottom: var(--space-4);
}

.legal-chat-page__messages {
  display: grid;
  gap: var(--space-8);
}

.legal-message {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: var(--space-3);
  align-items: start;
}

.legal-message--user {
  grid-template-columns: minmax(0, 1fr);
  max-width: min(72%, 520px);
  margin-left: auto;
}

.legal-message--user .legal-message__avatar {
  display: none;
}

.legal-message--user .legal-message__body {
  grid-column: 1;
  grid-row: 1;
  justify-self: end;
  color: var(--color-text);
  background: var(--color-surface-muted);
  border-color: transparent;
  border-radius: 14px;
  box-shadow: none;
}

.legal-message--assistant .legal-message__avatar {
  align-self: end;
  color: var(--color-primary);
  background: transparent;
  font-size: 0;
}

.legal-message--system .legal-message__avatar,
.legal-message--system .legal-message__body {
  background: var(--color-warning-soft);
}

.legal-message__avatar {
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

.legal-message--assistant .legal-message__avatar::before {
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

.legal-message__body {
  max-width: 100%;
  padding: var(--space-4);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}

.legal-message--assistant .legal-message__body {
  padding: 0 0 var(--space-2);
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.legal-message__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.legal-message--assistant .legal-message__meta {
  justify-content: flex-start;
  color: var(--color-text-subtle);
}

.legal-message--user .legal-message__meta {
  display: none;
}

.legal-message__content {
  line-height: var(--line-relaxed);
  overflow-wrap: anywhere;
}

.legal-message__citations {
  margin-top: var(--space-3);
  color: var(--color-text-muted);
}

.legal-message__citations summary {
  cursor: pointer;
  font-size: var(--text-sm);
}

.legal-message__citations blockquote {
  margin: var(--space-2) 0 0;
  padding: var(--space-3);
  background: var(--color-surface-muted);
  border-left: 3px solid var(--color-legal);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.legal-message__citations p {
  margin-top: var(--space-2);
}

.legal-message__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin-top: var(--space-4);
}

.legal-message__actions .el-button {
  width: 28px;
  height: 28px;
  margin: 0;
  color: var(--color-text-subtle);
}

.legal-message__actions .el-button:hover {
  color: var(--color-text);
  background: var(--color-surface-muted);
}

.legal-chat-page__composer-shell {
  position: sticky;
  bottom: var(--space-4);
  z-index: var(--z-sticky);
  display: grid;
  gap: var(--space-3);
  padding-top: var(--space-4);
  background: linear-gradient(180deg, transparent, var(--color-bg) 34%);
}

.legal-chat-page__risk {
  border-radius: var(--radius-md);
}

@media (max-width: 767px) {
  .legal-chat-page {
    gap: var(--space-4);
  }

  .legal-chat-page__topbar {
    align-items: flex-start;
  }

  .legal-message,
  .legal-message--user {
    grid-template-columns: 32px minmax(0, 1fr);
    max-width: 100%;
  }

  .legal-message--user .legal-message__avatar {
    display: none;
  }

  .legal-message--user .legal-message__body {
    grid-column: 1 / -1;
  }

  .legal-message__avatar {
    width: 32px;
    height: 32px;
  }
}
</style>
