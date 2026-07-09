<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { legalClient } from '@api/legal';
import ChatComposer from '@components/chat/ChatComposer.vue';
import ThinkingPanel from '@components/chat/ThinkingPanel.vue';
import EmptyState from '@components/ui/EmptyState.vue';
import AppIcon from '@components/ui/AppIcon.vue';
import LoadingState from '@components/ui/LoadingState.vue';
import SafeMarkdown from '@components/ui/SafeMarkdown.vue';
import SSEStatusIndicator from '@components/ui/SSEStatusIndicator.vue';
import { useToastStore } from '@stores/toast';
import { createConversationTitle } from '@lib/conversation-title';
import { useAgentStream } from '@/composables/useAgentStream';
import { useTypewriter } from '@/composables/useTypewriter';
import type { LegalMessage } from '@/types/legal';

const route = useRoute();
const router = useRouter();
const toast = useToastStore();

const sessionPublicId = computed(() => String(route.params.id));
const messages = ref<LegalMessage[]>([]);
const loadingMessages = ref(false);
const submitting = ref(false);
const question = ref(typeof route.query.q === 'string' ? route.query.q : '');
const pendingQuestion = ref('');
const pendingIsFirstExchange = ref(false);
const feedbackDialogVisible = ref(false);
const reviewDialogVisible = ref(false);
const selectedMessage = ref<LegalMessage | null>(null);
const feedbackRating = ref(5);
const feedbackComment = ref('');
const reviewReason = ref('');
const secondarySubmitting = ref(false);
const conversationRef = ref<HTMLElement | null>(null);
const conversationScrolling = ref(false);
let conversationScrollTimer: number | undefined;

// STREAM-100: shared thinking/answer stream state machine + component.
const {
  phase: streamPhase,
  thinkingText,
  answerText,
  thinkingElapsedSeconds,
  thinkingDurationMs,
  panelExpanded,
  streamState,
  errorMessage: streamError,
  isStreaming,
  start: startStream,
  stop: stopStream,
  reset: resetStream,
  togglePanel,
} = useAgentStream({
  createClient: ({ onEvent, onStateChange }) =>
    legalClient.createQuestionStream({
      sessionPublicId: sessionPublicId.value,
      question: pendingQuestion.value,
      onEvent,
      onStateChange,
    }),
});
const { displayed: displayedAnswer, flush: flushAnswer } = useTypewriter(answerText);

const sessionTitle = computed(() => {
  const firstUserMessage = messages.value.find((message) => message.role === 'user');
  return createConversationTitle(
    pendingQuestion.value || question.value || firstUserMessage?.content,
    '新的法律咨询',
  );
});
const lastHighRiskMessage = computed(() => {
  const assistants = messages.value.filter((message) => message.role === 'assistant');
  const last = assistants.at(-1);
  return last?.high_risk ? last : null;
});

watch(streamPhase, (phase) => {
  if (phase === 'done') {
    flushAnswer();
    submitting.value = false;
    void (async () => {
      await loadMessages();
      pendingQuestion.value = '';
      resetStream();
      toast.success('已回复');
      // After the first exchange, auto-name the session (LLM + fallback). Fire and
      // forget: naming must never disrupt the conversation.
      if (pendingIsFirstExchange.value) {
        pendingIsFirstExchange.value = false;
        void legalClient.generateSessionTitle(sessionPublicId.value).catch(() => {});
      }
    })();
  } else if (phase === 'error') {
    submitting.value = false;
    toast.error(streamError.value || '流式连接中断，请重试');
  }
});

watch(
  () => [messages.value.length, pendingQuestion.value, displayedAnswer.value, streamPhase.value],
  () => scrollConversationToBottom(),
  { flush: 'post' },
);

function scrollConversationToBottom(): void {
  const target = conversationRef.value;
  if (!target) return;
  requestAnimationFrame(() => {
    target.scrollTop = target.scrollHeight;
  });
}

function handleConversationScroll(): void {
  conversationScrolling.value = true;
  if (conversationScrollTimer) {
    window.clearTimeout(conversationScrollTimer);
  }
  conversationScrollTimer = window.setTimeout(() => {
    conversationScrolling.value = false;
  }, 900);
}

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

  pendingIsFirstExchange.value = messages.value.length === 0;
  submitting.value = true;
  resetStream();
  pendingQuestion.value = normalized;
  question.value = '';
  try {
    startStream();
  } catch (error) {
    submitting.value = false;
    toast.error(error instanceof Error ? error.message : '发送失败，请重试');
  }
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
  stopStream();
  if (conversationScrollTimer) {
    window.clearTimeout(conversationScrollTimer);
  }
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

    <main
      ref="conversationRef"
      class="legal-chat-page__conversation"
      :class="{ 'legal-chat-page__conversation--scrolling': conversationScrolling }"
      aria-label="法律对话"
      @scroll="handleConversationScroll"
    >
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
                message.role === 'assistant' ? '法律助手' : message.role === 'system' ? '系统' : '我'
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
          v-if="pendingQuestion || isStreaming || answerText"
          class="legal-message legal-message--assistant legal-message--pending"
        >
          <div class="legal-message__avatar" aria-hidden="true">AI</div>
          <div class="legal-message__body">
            <ThinkingPanel
              :thinking="thinkingText"
              :phase="streamPhase"
              :elapsed-seconds="thinkingElapsedSeconds"
              :duration-ms="thinkingDurationMs"
              :expanded="panelExpanded"
              tone="legal"
              @toggle="togglePanel"
            />
            <div class="legal-message__content">
              <SafeMarkdown v-if="answerText" :source="displayedAnswer" />
              <p v-else-if="streamPhase === 'thinking'">正在思考…</p>
              <p v-else-if="streamPhase === 'error'">{{ streamError || '生成失败，请重试' }}</p>
              <p v-else>正在生成…</p>
            </div>
          </div>
        </article>
      </div>
    </main>

    <footer class="legal-chat-page__composer-shell" aria-label="发送问题">
      <el-alert
        v-if="lastHighRiskMessage"
        class="legal-chat-page__risk"
        type="warning"
        title="这类问题建议再做人工确认"
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
  width: min(100%, 980px);
  max-width: 980px;
  height: calc(100dvh - var(--layout-header-height) - var(--space-5) - var(--space-8));
  min-height: 0;
  margin: 0 auto;
  overflow: hidden;
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
  min-height: 0;
  padding: var(--space-2) var(--space-1) var(--space-5);
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-color: transparent transparent;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  transition: scrollbar-color var(--duration-fast) var(--ease-in-out);
}

.legal-chat-page__conversation:hover,
.legal-chat-page__conversation--scrolling {
  scrollbar-color: color-mix(in oklch, var(--color-text-subtle) 48%, transparent) transparent;
}

.legal-chat-page__conversation::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.legal-chat-page__conversation::-webkit-scrollbar-track {
  background: transparent;
}

.legal-chat-page__conversation::-webkit-scrollbar-thumb {
  background: transparent;
  border: 2px solid transparent;
  border-radius: var(--radius-pill);
  background-clip: content-box;
}

.legal-chat-page__conversation:hover::-webkit-scrollbar-thumb,
.legal-chat-page__conversation--scrolling::-webkit-scrollbar-thumb {
  background-color: color-mix(in oklch, var(--color-text-subtle) 48%, transparent);
}

.legal-chat-page__conversation::-webkit-scrollbar-thumb:hover {
  background-color: color-mix(in oklch, var(--color-text-muted) 62%, transparent);
}

.legal-chat-page__messages {
  display: grid;
  gap: var(--space-8);
  align-content: start;
  padding-right: var(--space-2);
}

.legal-message {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: var(--space-3);
  align-items: start;
  animation: legal-message-rise 400ms var(--ease-out-expo) both;
}

@keyframes legal-message-rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  color: currentColor;
  background: var(--color-primary-soft);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 750;
  content: 'AI';
}

.legal-message--pending .legal-message__avatar::before {
  width: 24px;
  height: 24px;
  background: repeating-conic-gradient(
    from 0deg,
    currentColor 0deg 10deg,
    transparent 10deg 22.5deg
  );
  color: var(--color-primary);
  content: '';
  animation: legal-pending-spin 1.2s linear infinite;
}

@keyframes legal-pending-spin {
  to {
    transform: rotate(360deg);
  }
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
  position: relative;
  z-index: var(--z-sticky);
  display: grid;
  gap: var(--space-3);
  padding-top: var(--space-4);
  background: var(--color-bg);
}

.legal-chat-page__risk {
  border-radius: var(--radius-md);
}

@media (max-width: 767px) {
  .legal-chat-page {
    gap: var(--space-4);
    height: calc(100dvh - 64px - var(--space-4) - var(--space-6));
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
