<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { recruitmentClient } from '@api/recruitment';
import ThinkingPanel from '@components/chat/ThinkingPanel.vue';
import AsyncState from '@components/ui/AsyncState.vue';
import SafeMarkdown from '@components/ui/SafeMarkdown.vue';
import SSEStatusIndicator from '@components/ui/SSEStatusIndicator.vue';
import { useAuthStore } from '@stores/auth';
import { useToastStore } from '@stores/toast';
import { useAgentStream } from '@/composables/useAgentStream';
import { useTypewriter } from '@/composables/useTypewriter';
import type { AgentStreamClient } from '@lib/sse-client';
import {
  createErrorState,
  createLoadingState,
  createSuccessState,
  toRequestError,
} from '@lib/request-state';
import type { RequestState } from '@/types/request-state';
import type { AgentStreamEvent, StreamState } from '@/types/sse';
import type {
  RecruitRun,
  RecruitTaskDetail,
  RecruitReviewStatus,
  RecruitRunStatus,
  RecruitTaskStatus,
} from '@/types/recruitment';

const route = useRoute();
const router = useRouter();
const toast = useToastStore();
const auth = useAuthStore();

const taskId = computed(() => String(route.params.id));
const isAdmin = computed(() => auth.profile?.role === 'admin');
const reviewing = ref(false);

const state = ref<RequestState<RecruitTaskDetail>>({
  status: 'idle',
  data: null,
  error: null,
  updatedAt: null,
});

const run = ref<RecruitRun | null>(null);
const streamState = ref<StreamState>('idle');
const nodeTrace = ref<string[]>([]);
const running = ref(false);
const reportBusy = ref(false);
const conversationRef = ref<HTMLElement | null>(null);
const conversationScrolling = ref(false);

let stream: AgentStreamClient | null = null;
let conversationScrollTimer: number | undefined;

// STREAM-100: live thinking/analysis stream via the shared state machine + panel.
const {
  phase: analysisPhase,
  thinkingText,
  answerText,
  thinkingElapsedSeconds,
  thinkingDurationMs,
  panelExpanded,
  errorMessage: analysisError,
  isStreaming: analysisStreaming,
  start: startAnalysisStream,
  stop: stopAnalysisStream,
  reset: resetAnalysisStream,
  togglePanel: toggleAnalysisPanel,
} = useAgentStream({
  createClient: ({ onEvent, onStateChange }) =>
    recruitmentClient.createRunCompletionStream({
      taskId: taskId.value,
      onEvent,
      onStateChange,
    }),
});
const { displayed: displayedAnalysis, flush: flushAnalysis } = useTypewriter(answerText);

watch(analysisPhase, (phase) => {
  if (phase === 'done') flushAnalysis();
  scrollConversationToBottom();
});

watch(
  () => [
    nodeTrace.value.length,
    displayedAnalysis.value,
    analysisPhase.value,
    run.value?.status,
    state.value.status,
  ],
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

const STATUS_LABEL: Record<RecruitTaskStatus, string> = {
  uploaded: '已上传',
  parsing: '解析中',
  parsed: '已解析',
  matching: '匹配中',
  reviewing: '复核中',
  completed: '已完成',
  failed: '失败',
};

const REVIEW_LABEL: Record<RecruitReviewStatus, string> = {
  pending: '待复核',
  approved: '已通过',
  rejected: '已驳回',
  changes_requested: '待修改',
};

const RUN_LABEL: Record<RecruitRunStatus, string> = {
  pending: '待执行',
  running: '运行中',
  success: '成功',
  failed: '失败',
  retrying: '重试中',
  canceled: '已取消',
};

const canReport = computed(() => state.value.data?.review_status === 'approved');
const canCancelRun = computed(
  () => run.value?.status === 'running' || run.value?.status === 'pending',
);
const assistantRunText = computed(() => {
  if (!run.value) return '材料已进入任务对话，可以开始候选人与岗位匹配分析。';
  if (run.value.status === 'success') return '分析已完成，可以继续复核并生成报告。';
  if (run.value.status === 'failed') return '分析运行失败，可以重新运行。';
  if (run.value.status === 'canceled') return '分析已取消，可以重新运行。';
  return `当前分析状态：${RUN_LABEL[run.value.status]}。`;
});
const reportText = computed(() =>
  canReport.value ? '复核已通过，可以生成匹配报告。' : '报告需要管理员复核通过后才能生成。',
);

function materialKindLabel(kind: string): string {
  if (kind === 'resume') return '简历';
  if (kind === 'jd') return '岗位说明';
  return kind;
}

async function loadTask(): Promise<void> {
  state.value = createLoadingState();
  try {
    const response = await recruitmentClient.getTask(taskId.value);
    state.value = createSuccessState(response.task);
    if (response.task.latest_run_id) {
      await refreshRun(response.task.latest_run_id);
    }
  } catch (error) {
    state.value = createErrorState(toRequestError(error));
  }
}

async function refreshRun(runId: string): Promise<void> {
  try {
    const response = await recruitmentClient.getRun(runId);
    run.value = response.run;
    nodeTrace.value = [...response.run.node_trace];
  } catch {
    // 运行详情缺失不阻塞任务展示
  }
}

async function startRun(): Promise<void> {
  running.value = true;
  nodeTrace.value = [];
  resetAnalysisStream();
  try {
    const response = await recruitmentClient.startRun(taskId.value);
    run.value = response.run;
    openStream(response.run.run_id);
    startAnalysisStream();
    toast.success('分析已开始');
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '启动失败，请重试');
  } finally {
    running.value = false;
  }
}

function openStream(runId: string): void {
  closeStream();
  stream = recruitmentClient.createRunStream({
    runId,
    onEvent: handleEvent,
    onStateChange: (next) => {
      streamState.value = next;
    },
  });
  stream.start();
}

function handleEvent(event: AgentStreamEvent): void {
  const eventName = event.event ?? '';
  const payload = (event.payload ?? {}) as Record<string, unknown>;
  const node = typeof payload.node_name === 'string' ? payload.node_name : null;

  if (eventName === 'node.completed' && node) {
    if (!nodeTrace.value.includes(node)) {
      nodeTrace.value = [...nodeTrace.value, node];
    }
  }

  if (eventName === 'run.completed' || eventName === 'run.failed' || eventName === 'run.canceled') {
    closeStream();
    void loadTask();
  }
}

function closeStream(): void {
  if (stream) {
    stream.stop();
    stream = null;
  }
}

async function cancelRun(): Promise<void> {
  if (!run.value) return;
  try {
    const response = await recruitmentClient.cancelRun(run.value.run_id);
    run.value = response.run;
    closeStream();
    stopAnalysisStream();
    toast.info('已取消运行');
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '取消失败');
  }
}

async function generateReport(): Promise<void> {
  reportBusy.value = true;
  try {
    const response = await recruitmentClient.createReport(taskId.value);
    toast.success('报告已生成');
    await router.push({
      name: 'recruit-report-detail',
      params: { id: response.report.report_id },
    });
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '生成失败，需先通过复核');
  } finally {
    reportBusy.value = false;
  }
}

async function submitReview(reviewStatus: RecruitReviewStatus): Promise<void> {
  reviewing.value = true;
  try {
    await recruitmentClient.reviewTask(taskId.value, { review_status: reviewStatus });
    toast.success(reviewStatus === 'approved' ? '已通过复核' : '已驳回');
    await loadTask();
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '复核失败，请重试');
  } finally {
    reviewing.value = false;
  }
}

function back(): void {
  void router.push({ name: 'recruit-tasks' });
}

onMounted(() => {
  void loadTask();
});

onBeforeUnmount(() => {
  closeStream();
  stopAnalysisStream();
  if (conversationScrollTimer) {
    window.clearTimeout(conversationScrollTimer);
  }
});
</script>

<template>
  <div class="recruit-detail">
    <AsyncState :state="state" loading-message="加载任务中…" @retry="loadTask">
      <template #default="{ data }">
        <section v-if="data" class="recruit-detail__thread">
          <header class="recruit-detail__topbar">
            <button class="recruit-detail__back" type="button" @click="back">← 任务列表</button>
            <div class="recruit-detail__title">
              <h1>{{ data.title || '未命名任务' }}</h1>
              <div class="recruit-detail__tags">
                <el-tag effect="light">{{ STATUS_LABEL[data.status] }}</el-tag>
                <el-tag effect="plain">{{ REVIEW_LABEL[data.review_status] }}</el-tag>
              </div>
            </div>
          </header>

          <div
            ref="conversationRef"
            class="recruit-detail__messages"
            :class="{ 'recruit-detail__messages--scrolling': conversationScrolling }"
            @scroll="handleConversationScroll"
          >
            <article class="recruit-detail__message recruit-detail__message--user">
              <span class="recruit-detail__avatar">我</span>
              <div class="recruit-detail__bubble">
                <p class="recruit-detail__message-title">分析这个候选人与岗位的匹配度。</p>
                <dl class="recruit-detail__materials">
                  <div v-for="material in data.materials" :key="material.material_id">
                    <dt>{{ materialKindLabel(material.kind) }}</dt>
                    <dd>
                      扫描：{{ material.scan_status }} · {{ material.size_chars }} 字
                      <span v-if="material.original_deleted">· 原文已删除</span>
                    </dd>
                  </div>
                  <p v-if="data.materials.length === 0" class="recruit-detail__hint">
                    暂无材料元数据。
                  </p>
                </dl>
              </div>
            </article>

            <article class="recruit-detail__message recruit-detail__message--assistant">
              <span class="recruit-detail__avatar">招</span>
              <div class="recruit-detail__bubble">
                <div class="recruit-detail__message-head">
                  <span>招聘助手</span>
                  <SSEStatusIndicator v-if="streamState !== 'idle'" :state="streamState" />
                </div>
                <p>{{ assistantRunText }}</p>
                <div class="recruit-detail__actions">
                  <el-button type="primary" :loading="running" @click="startRun">
                    {{ run ? '重新运行' : '开始分析' }}
                  </el-button>
                  <el-button v-if="canCancelRun" @click="cancelRun">取消</el-button>
                  <el-tag v-if="run" effect="light">{{ RUN_LABEL[run.status] }}</el-tag>
                  <span v-if="run?.error_code" class="recruit-detail__error">
                    {{ run.error_code }}
                  </span>
                </div>
              </div>
            </article>

            <article
              v-if="nodeTrace.length > 0"
              class="recruit-detail__message recruit-detail__message--assistant"
            >
              <span class="recruit-detail__avatar">招</span>
              <div class="recruit-detail__bubble">
                <p class="recruit-detail__message-title">分析进度</p>
                <ol class="recruit-detail__trace" aria-label="节点轨迹">
                  <li v-for="node in nodeTrace" :key="node">{{ node }}</li>
                </ol>
              </div>
            </article>

            <article
              v-if="data.analysis"
              class="recruit-detail__message recruit-detail__message--assistant"
            >
              <span class="recruit-detail__avatar">招</span>
              <div class="recruit-detail__bubble">
                <p class="recruit-detail__message-title">匹配摘要</p>
                <div class="recruit-detail__analysis-score">
                  <strong>{{ data.analysis.match_score }}</strong>
                  <span>/100 · {{ data.analysis.match_tier }}</span>
                </div>
                <p>{{ data.analysis.candidate_summary }}</p>
                <dl class="recruit-detail__analysis-list">
                  <div>
                    <dt>岗位</dt>
                    <dd>{{ data.analysis.job_title || '未识别' }}</dd>
                  </div>
                  <div>
                    <dt>命中关键词</dt>
                    <dd>{{ data.analysis.matched_keywords.join('、') || '无' }}</dd>
                  </div>
                  <div>
                    <dt>待追问缺口</dt>
                    <dd>{{ data.analysis.missing_keywords.join('、') || '无' }}</dd>
                  </div>
                </dl>
                <div class="recruit-detail__analysis-block">
                  <span>风险点</span>
                  <ul>
                    <li v-for="risk in data.analysis.risk_points" :key="risk">{{ risk }}</li>
                  </ul>
                </div>
                <div class="recruit-detail__analysis-block">
                  <span>面试问题</span>
                  <ul>
                    <li v-for="question in data.analysis.interview_questions" :key="question">
                      {{ question }}
                    </li>
                  </ul>
                </div>
                <p class="recruit-detail__hint">{{ data.analysis.fairness_note }}</p>
              </div>
            </article>

            <article
              v-if="analysisStreaming || answerText || analysisPhase === 'error'"
              class="recruit-detail__message recruit-detail__message--assistant"
            >
              <span class="recruit-detail__avatar">招</span>
              <div class="recruit-detail__bubble recruit-detail__bubble--analysis">
                <ThinkingPanel
                  :thinking="thinkingText"
                  :phase="analysisPhase"
                  :elapsed-seconds="thinkingElapsedSeconds"
                  :duration-ms="thinkingDurationMs"
                  :expanded="panelExpanded"
                  tone="recruit"
                  @toggle="toggleAnalysisPanel"
                />
                <SafeMarkdown v-if="answerText" :source="displayedAnalysis" />
                <p v-else-if="analysisPhase === 'thinking'" class="recruit-detail__hint">
                  正在思考…
                </p>
                <p v-else-if="analysisPhase === 'error'" class="recruit-detail__error">
                  {{ analysisError || '分析失败，请重试' }}
                </p>
              </div>
            </article>

            <article class="recruit-detail__message recruit-detail__message--assistant">
              <span class="recruit-detail__avatar">招</span>
              <div class="recruit-detail__bubble">
                <p class="recruit-detail__message-title">复核与报告</p>
                <p class="recruit-detail__hint">{{ reportText }}</p>
                <div class="recruit-detail__actions">
                  <template v-if="isAdmin && data.review_status === 'pending'">
                    <el-button
                      type="success"
                      :loading="reviewing"
                      @click="submitReview('approved')"
                    >
                      通过复核
                    </el-button>
                    <el-button :loading="reviewing" @click="submitReview('rejected')">
                      驳回
                    </el-button>
                  </template>
                  <el-button
                    type="primary"
                    plain
                    :loading="reportBusy"
                    :disabled="!canReport"
                    @click="generateReport"
                  >
                    生成报告
                  </el-button>
                </div>
              </div>
            </article>
          </div>
        </section>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.recruit-detail {
  width: min(100%, 980px);
  max-width: 980px;
  height: calc(100dvh - var(--layout-header-height) - var(--space-5) - var(--space-8));
  min-height: 0;
  margin: 0 auto;
  overflow: hidden;
}

.recruit-detail__thread {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: var(--space-4);
  height: 100%;
  min-height: 0;
}

.recruit-detail__topbar {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: var(--space-4);
  padding: 0 var(--space-1);
}

.recruit-detail__back {
  padding: var(--space-1) 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  background: none;
  border: none;
  cursor: pointer;
}

.recruit-detail__title {
  display: grid;
  gap: var(--space-2);
  min-width: 0;
}

.recruit-detail__title h1 {
  overflow-wrap: anywhere;
  font-size: var(--text-xl);
  font-weight: 650;
}

.recruit-detail__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.recruit-detail__messages {
  display: grid;
  align-content: start;
  gap: var(--space-8);
  min-height: 0;
  padding: var(--space-2) var(--space-3) var(--space-5) var(--space-1);
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-color: transparent transparent;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  transition: scrollbar-color var(--duration-fast) var(--ease-in-out);
}

.recruit-detail__messages:hover,
.recruit-detail__messages--scrolling {
  scrollbar-color: color-mix(in oklch, var(--color-text-subtle) 48%, transparent) transparent;
}

.recruit-detail__messages::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.recruit-detail__messages::-webkit-scrollbar-track {
  background: transparent;
}

.recruit-detail__messages::-webkit-scrollbar-thumb {
  background: transparent;
  border: 2px solid transparent;
  border-radius: var(--radius-pill);
  background-clip: content-box;
}

.recruit-detail__messages:hover::-webkit-scrollbar-thumb,
.recruit-detail__messages--scrolling::-webkit-scrollbar-thumb {
  background-color: color-mix(in oklch, var(--color-text-subtle) 48%, transparent);
}

.recruit-detail__messages::-webkit-scrollbar-thumb:hover {
  background-color: color-mix(in oklch, var(--color-text-muted) 62%, transparent);
}

.recruit-detail__message {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: var(--space-3);
  align-items: start;
  animation: recruit-message-rise 400ms var(--ease-out-expo) both;
}

@keyframes recruit-message-rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.recruit-detail__message--user {
  grid-template-columns: minmax(0, 1fr);
  max-width: min(72%, 620px);
  margin-left: auto;
}

.recruit-detail__message--user .recruit-detail__avatar {
  display: none;
}

.recruit-detail__avatar {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 700;
}

.recruit-detail__message--assistant .recruit-detail__avatar {
  align-self: end;
  color: var(--color-recruit);
  background: transparent;
  font-size: 0;
}

.recruit-detail__message--assistant .recruit-detail__avatar::before {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  color: var(--color-recruit);
  background: var(--color-recruit-soft);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 750;
  content: 'AI';
}

.recruit-detail__bubble {
  display: grid;
  gap: var(--space-3);
  width: min(100%, 760px);
  max-width: 100%;
  padding: 0 0 var(--space-2);
  color: var(--color-text);
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  line-height: var(--line-relaxed);
}

.recruit-detail__message--user .recruit-detail__bubble {
  justify-self: end;
  width: min(100%, 680px);
  padding: var(--space-4);
  background: var(--color-surface-muted);
  border-radius: 14px;
}

.recruit-detail__bubble--analysis {
  gap: var(--space-4);
}

.recruit-detail__message-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
}

.recruit-detail__message-title {
  font-weight: 700;
}

.recruit-detail__materials {
  display: grid;
  gap: var(--space-2);
}

.recruit-detail__materials div {
  display: grid;
  gap: var(--space-1);
}

.recruit-detail__materials dt {
  font-weight: 600;
}

.recruit-detail__materials dd {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.recruit-detail__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.recruit-detail__error {
  color: var(--color-danger);
  font-size: var(--text-sm);
}

.recruit-detail__trace {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding-left: 0;
  list-style: none;
}

.recruit-detail__trace li {
  padding: var(--space-1) var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
}

.recruit-detail__hint {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.recruit-detail__analysis-score {
  display: inline-flex;
  align-items: baseline;
  gap: var(--space-1);
  width: fit-content;
  padding: var(--space-2) var(--space-3);
  color: var(--color-recruit);
  background: var(--color-recruit-soft);
  border-radius: var(--radius-md);
}

.recruit-detail__analysis-score strong {
  font-size: 1.45rem;
  line-height: 1;
}

.recruit-detail__analysis-list {
  display: grid;
  gap: var(--space-2);
}

.recruit-detail__analysis-list div {
  display: grid;
  grid-template-columns: 104px minmax(0, 1fr);
  gap: var(--space-3);
}

.recruit-detail__analysis-list dt,
.recruit-detail__analysis-block span {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
}

.recruit-detail__analysis-list dd {
  min-width: 0;
  overflow-wrap: anywhere;
}

.recruit-detail__analysis-block {
  display: grid;
  gap: var(--space-2);
}

.recruit-detail__analysis-block ul {
  display: grid;
  gap: var(--space-1);
  margin: 0;
  padding-left: var(--space-5);
}

@media (max-width: 767px) {
  .recruit-detail {
    height: calc(100dvh - 64px - var(--space-4) - var(--space-6));
    max-width: 100%;
  }

  .recruit-detail__topbar {
    grid-template-columns: 1fr;
    gap: var(--space-2);
  }

  .recruit-detail__title h1 {
    font-size: var(--text-lg);
  }

  .recruit-detail__message,
  .recruit-detail__message--user {
    grid-template-columns: 32px minmax(0, 1fr);
    max-width: 100%;
  }

  .recruit-detail__avatar {
    width: 32px;
    height: 32px;
  }

  .recruit-detail__message--user .recruit-detail__avatar {
    display: none;
  }

  .recruit-detail__message--user .recruit-detail__bubble {
    grid-column: 1 / -1;
  }
}
</style>
