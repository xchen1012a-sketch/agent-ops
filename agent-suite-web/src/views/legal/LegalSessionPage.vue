<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { legalClient } from '@api/legal';
import EmptyState from '@components/ui/EmptyState.vue';
import LoadingState from '@components/ui/LoadingState.vue';
import SafeMarkdown from '@components/ui/SafeMarkdown.vue';
import { useToastStore } from '@stores/toast';
import type { LegalMessage, LegalQuestionAnswer } from '@/types/legal';

const route = useRoute();
const toast = useToastStore();

const sessionPublicId = computed(() => String(route.params.id));
const messages = ref<LegalMessage[]>([]);
const answerTrace = ref<string[]>([]);
const currentAnswer = ref<LegalQuestionAnswer | null>(null);
const loadingMessages = ref(false);
const submitting = ref(false);
const question = ref('');
const feedbackDialogVisible = ref(false);
const reviewDialogVisible = ref(false);
const selectedMessage = ref<LegalMessage | null>(null);
const feedbackRating = ref(5);
const feedbackComment = ref('');
const reviewReason = ref('');
const secondarySubmitting = ref(false);

async function loadMessages(): Promise<void> {
  loadingMessages.value = true;
  try {
    const response = await legalClient.listMessages(sessionPublicId.value, {
      limit: 50,
      offset: 0,
    });
    messages.value = response.data.items;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载会话消息失败');
  } finally {
    loadingMessages.value = false;
  }
}

async function submitQuestion(): Promise<void> {
  const normalized = question.value.trim();
  if (!normalized) return;

  submitting.value = true;
  try {
    const response = await legalClient.answerQuestion(sessionPublicId.value, {
      question: normalized,
    });
    currentAnswer.value = response.data;
    answerTrace.value = response.data.node_trace;
    question.value = '';
    await loadMessages();
    toast.success('法律咨询回答已生成');
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '提交问题失败，请稍后重试');
  } finally {
    submitting.value = false;
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

function openReviewDialog(message: LegalMessage): void {
  selectedMessage.value = message;
  reviewReason.value = message.high_risk ? '高风险法律咨询需要人工复核' : '';
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
    toast.success('反馈已提交');
    feedbackDialogVisible.value = false;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '提交反馈失败');
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
    toast.success('已加入高风险审核队列');
    reviewDialogVisible.value = false;
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '提交高风险审核失败');
  } finally {
    secondarySubmitting.value = false;
  }
}

onMounted(() => {
  void loadMessages();
});
</script>

<template>
  <div class="legal-session-page">
    <section class="legal-session-page__header" aria-labelledby="legal-session-title">
      <div>
        <p class="legal-session-page__eyebrow">法律咨询会话</p>
        <h1 id="legal-session-title">会话 {{ sessionPublicId }}</h1>
        <p class="legal-session-page__description">
          当前接入法律 Agent deterministic 问答接口。真实 DeepSeek/RAG/Token
          流式能力仍以后端后续集成为准。
        </p>
      </div>
      <el-button :loading="loadingMessages" @click="loadMessages">刷新消息</el-button>
    </section>

    <section class="legal-session-page__layout">
      <article class="legal-session-page__conversation" aria-label="会话消息">
        <LoadingState v-if="loadingMessages" message="正在加载会话消息…" />
        <EmptyState
          v-else-if="messages.length === 0"
          title="暂无消息"
          description="在右侧输入法律问题，提交后会保存用户问题与助手回答。"
          icon="ChatDotRound"
        />
        <div v-else class="legal-session-page__messages">
          <div
            v-for="message in messages"
            :key="message.public_id"
            class="legal-message"
            :class="`legal-message--${messageTone(message.role)}`"
          >
            <div class="legal-message__meta">
              <strong>{{ message.role === 'assistant' ? '法律助手' : '用户' }}</strong>
              <el-tag v-if="message.high_risk" type="warning" effect="light">高风险</el-tag>
            </div>
            <SafeMarkdown :source="message.content" />
            <div v-if="message.citations?.length" class="legal-message__citations">
              <h3>引用来源</h3>
              <blockquote v-for="citation in message.citations" :key="citation.snippet">
                <strong>{{ citation.source ?? '未知来源' }}</strong>
                <span v-if="citation.section"> · {{ citation.section }}</span>
                <p>{{ citation.snippet }}</p>
              </blockquote>
            </div>
            <div v-if="message.role === 'assistant'" class="legal-message__actions">
              <el-button size="small" @click="openFeedbackDialog(message)">反馈</el-button>
              <el-button size="small" type="warning" plain @click="openReviewDialog(message)">
                加入高风险审核
              </el-button>
            </div>
          </div>
        </div>
      </article>

      <aside class="legal-session-page__panel" aria-label="提交法律问题">
        <el-form label-position="top" @submit.prevent="submitQuestion">
          <el-form-item label="法律问题" required>
            <el-input
              v-model="question"
              type="textarea"
              :rows="8"
              maxlength="4000"
              show-word-limit
              resize="vertical"
              placeholder="请描述你的法律问题，例如：公司单方面调岗，我可以拒绝吗？"
            />
          </el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="submitting"
            :disabled="!question.trim()"
          >
            提交问题
          </el-button>
        </el-form>

        <div v-if="currentAnswer" class="legal-session-page__answer-summary">
          <h2>本次回答摘要</h2>
          <el-alert
            v-if="currentAnswer.high_risk"
            type="warning"
            :title="currentAnswer.risk_reason ?? '该问题需要线下专业咨询'"
            show-icon
            :closable="false"
          />
          <p v-if="currentAnswer.category">分类：{{ currentAnswer.category }}</p>
          <p>引用数：{{ currentAnswer.citations.length }}</p>
        </div>

        <div v-if="answerTrace.length" class="legal-session-page__trace">
          <h2>节点轨迹</h2>
          <ol>
            <li v-for="node in answerTrace" :key="node">{{ node }}</li>
          </ol>
        </div>
      </aside>
    </section>

    <el-dialog v-model="feedbackDialogVisible" title="提交回答反馈" width="420px">
      <el-form label-position="top" @submit.prevent="submitFeedback">
        <el-form-item label="评分">
          <el-rate v-model="feedbackRating" :max="5" aria-label="回答评分" />
        </el-form-item>
        <el-form-item label="反馈说明">
          <el-input
            v-model="feedbackComment"
            type="textarea"
            :rows="4"
            maxlength="1000"
            show-word-limit
            placeholder="可选：说明回答是否有帮助、是否缺少引用或存在风险。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="secondarySubmitting" @click="submitFeedback">
          提交反馈
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewDialogVisible" title="加入高风险审核" width="460px">
      <el-alert
        type="warning"
        title="该操作会把助手回答加入管理员复核队列。"
        show-icon
        :closable="false"
      />
      <el-form class="legal-session-page__dialog-form" label-position="top">
        <el-form-item label="审核原因" required>
          <el-input
            v-model="reviewReason"
            type="textarea"
            :rows="4"
            maxlength="200"
            show-word-limit
            placeholder="例如：涉及人身安全、紧急救助或重大财产风险。"
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
          加入审核
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.legal-session-page {
  display: grid;
  gap: var(--space-6);
  max-width: var(--layout-content-max-width);
  margin: 0 auto;
}

.legal-session-page__header {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.legal-session-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-legal);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.legal-session-page__description {
  max-width: 760px;
  margin-top: var(--space-3);
  color: var(--color-text-muted);
}

.legal-session-page__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: var(--space-4);
  align-items: start;
}

.legal-session-page__conversation,
.legal-session-page__panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.legal-session-page__conversation {
  min-height: 520px;
  padding: var(--space-4);
}

.legal-session-page__panel {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
}

.legal-session-page__messages {
  display: grid;
  gap: var(--space-4);
}

.legal-message {
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.legal-message--assistant {
  background: var(--color-legal-soft);
}

.legal-message--user {
  margin-left: auto;
  max-width: 88%;
  background: var(--color-surface-muted);
}

.legal-message--system {
  background: var(--color-warning-soft);
}

.legal-message__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.legal-message__citations {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.legal-message__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.legal-message__citations h3,
.legal-session-page__answer-summary h2,
.legal-session-page__trace h2 {
  margin-bottom: var(--space-2);
  font-size: var(--text-base);
}

.legal-message__citations blockquote {
  margin: var(--space-2) 0 0;
  padding: var(--space-3);
  background: var(--color-surface);
  border-left: 4px solid var(--color-legal);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.legal-message__citations p {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.legal-session-page__answer-summary,
.legal-session-page__trace {
  display: grid;
  gap: var(--space-2);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.legal-session-page__trace ol {
  padding-left: var(--space-5);
  color: var(--color-text-muted);
}

.legal-session-page__dialog-form {
  margin-top: var(--space-4);
}

@media (max-width: 1023px) {
  .legal-session-page__layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .legal-session-page__header {
    align-items: flex-start;
    flex-direction: column;
    padding: var(--space-4);
  }

  .legal-message--user {
    max-width: 100%;
  }
}
</style>
