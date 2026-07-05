<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { recruitmentClient } from '@api/recruitment';
import AsyncState from '@components/ui/AsyncState.vue';
import SSEStatusIndicator from '@components/ui/SSEStatusIndicator.vue';
import { useToastStore } from '@stores/toast';
import type { AgentStreamClient } from '@lib/sse-client';
import { createErrorState, createLoadingState, createSuccessState } from '@lib/request-state';
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

const taskId = computed(() => String(route.params.id));

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

let stream: AgentStreamClient | null = null;

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

async function loadTask(): Promise<void> {
  state.value = createLoadingState();
  try {
    const response = await recruitmentClient.getTask(taskId.value);
    state.value = createSuccessState(response.task);
    if (response.task.latest_run_id) {
      await refreshRun(response.task.latest_run_id);
    }
  } catch (error) {
    state.value = createErrorState(error instanceof Error ? error : String(error ?? '加载失败'));
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
  try {
    const response = await recruitmentClient.startRun(taskId.value);
    run.value = response.run;
    openStream(response.run.run_id);
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

function back(): void {
  void router.push({ name: 'recruit-tasks' });
}

onMounted(() => {
  void loadTask();
});

onBeforeUnmount(() => {
  closeStream();
});
</script>

<template>
  <div class="recruit-detail">
    <button class="recruit-detail__back" type="button" @click="back">← 返回任务列表</button>

    <AsyncState :state="state" loading-message="加载任务中…" @retry="loadTask">
      <template #default="{ data }">
        <section v-if="data" class="recruit-detail__card">
          <header class="recruit-detail__head">
            <div>
              <p class="recruit-detail__eyebrow">招聘任务</p>
              <h1>{{ data.title || '未命名任务' }}</h1>
            </div>
            <div class="recruit-detail__tags">
              <el-tag effect="light">{{ STATUS_LABEL[data.status] }}</el-tag>
              <el-tag effect="plain">{{ REVIEW_LABEL[data.review_status] }}</el-tag>
            </div>
          </header>

          <dl class="recruit-detail__materials">
            <div v-for="material in data.materials" :key="material.material_id">
              <dt>
                {{
                  material.kind === 'resume'
                    ? '简历'
                    : material.kind === 'jd'
                      ? '岗位说明'
                      : material.kind
                }}
              </dt>
              <dd>
                扫描：{{ material.scan_status }} · {{ material.size_chars }} 字
                <span v-if="material.original_deleted">· 原文已删除</span>
              </dd>
            </div>
            <p v-if="data.materials.length === 0" class="recruit-detail__empty-materials">
              暂无材料元数据。
            </p>
          </dl>

          <section class="recruit-detail__run">
            <div class="recruit-detail__run-head">
              <h2>分析运行</h2>
              <SSEStatusIndicator v-if="streamState !== 'idle'" :state="streamState" />
            </div>

            <div class="recruit-detail__run-actions">
              <el-button type="primary" :loading="running" @click="startRun">
                {{ run ? '重新运行' : '开始分析' }}
              </el-button>
              <el-button
                v-if="run && (run.status === 'running' || run.status === 'pending')"
                @click="cancelRun"
              >
                取消
              </el-button>
              <el-tag v-if="run" effect="light">{{ RUN_LABEL[run.status] }}</el-tag>
              <span v-if="run?.error_code" class="recruit-detail__error">{{ run.error_code }}</span>
            </div>

            <ol v-if="nodeTrace.length > 0" class="recruit-detail__trace" aria-label="节点轨迹">
              <li v-for="node in nodeTrace" :key="node">{{ node }}</li>
            </ol>
          </section>

          <section class="recruit-detail__report">
            <h2>分析报告</h2>
            <p class="recruit-detail__hint">
              {{ canReport ? '任务已通过复核，可生成报告。' : '报告需管理员复核通过后才能生成。' }}
            </p>
            <el-button
              type="primary"
              plain
              :loading="reportBusy"
              :disabled="!canReport"
              @click="generateReport"
            >
              生成报告
            </el-button>
          </section>
        </section>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.recruit-detail {
  display: grid;
  gap: var(--space-4);
  max-width: 960px;
  margin: 0 auto;
}

.recruit-detail__back {
  justify-self: start;
  padding: var(--space-1) 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  background: none;
  border: none;
  cursor: pointer;
}

.recruit-detail__card {
  display: grid;
  gap: var(--space-5);
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.recruit-detail__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.recruit-detail__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-recruit, var(--color-primary));
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.recruit-detail__tags {
  display: flex;
  gap: var(--space-2);
}

.recruit-detail__materials {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-surface-muted);
  border-radius: var(--radius-md);
}

.recruit-detail__materials dt {
  font-weight: 600;
}

.recruit-detail__materials dd {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.recruit-detail__empty-materials {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.recruit-detail__run,
.recruit-detail__report {
  display: grid;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.recruit-detail__run-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.recruit-detail__run-head h2,
.recruit-detail__report h2 {
  font-size: var(--text-lg);
}

.recruit-detail__run-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
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
  font-size: var(--text-xs);
  background: var(--color-surface-muted);
  border-radius: var(--radius-pill);
}

.recruit-detail__hint {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

@media (max-width: 767px) {
  .recruit-detail__card {
    padding: var(--space-4);
  }

  .recruit-detail__head {
    flex-direction: column;
  }
}
</style>
